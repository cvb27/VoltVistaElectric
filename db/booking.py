"""Consultas sobre reservas.

Es el unico puente entre la base de datos y core/booking.py: traduce filas
en el diccionario `taken` que consume la logica de calendario.
"""

from datetime import datetime, timedelta

from sqlmodel import Session, select, update

from core.booking import HOLD_MINUTES
from db.models import Booking


def taken_map(session: Session) -> dict:
    """Cupos ocupados, en el formato que espera core/booking.py.

        {"2026-08-21": {1: 1, 3: 1}, ...}

    Cuenta dos cosas:
      - Las reservas pagadas. Esas ocupan siempre.
      - Las pendientes RECIENTES. Cuando alguien llega al checkout de
        Stripe se crea la reserva como "pending" y su cupo queda apartado
        mientras paga.

    Una pendiente vieja NO cuenta: si abandono el pago hace una hora, el
    cupo vuelve a estar libre. Por eso no hace falta ningun proceso que
    limpie reservas abandonadas — se liberan solas al dejar de contarse.

    El registro pending queda en la base como rastro del abandono, que
    despues sirve para saber cuantos llegan al checkout y no pagan.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=HOLD_MINUTES)

    rows = session.exec(
        select(Booking.service_date, Booking.slot, Booking.status, Booking.created_at)
        .where(Booking.status.in_(("paid", "pending")))
    ).all()

    out: dict = {}
    for service_date, slot, status, created_at in rows:
        if status == "pending" and created_at < cutoff:
            continue
        key = service_date.isoformat()
        out.setdefault(key, {})
        out[key][slot] = out[key].get(slot, 0) + 1
    return out


def get_by_public_id(session: Session, public_id: str) -> Booking | None:
    return session.exec(
        select(Booking).where(Booking.public_id == public_id)
    ).first()


def get_by_stripe_session(session: Session, session_id: str) -> Booking | None:
    return session.exec(
        select(Booking).where(Booking.stripe_session_id == session_id)
    ).first()


def mark_paid(session: Session, booking: Booking, customer_email: str = "") -> bool:
    """Pasa la reserva a "paid". Devuelve True solo la PRIMERA vez.

    Devolver True/False es lo que permite avisar al dueno una sola vez: hay
    dos caminos que confirman el pago — el webhook de Stripe y la pagina de
    confirmacion — y pueden llegar a la vez.

    Por eso el UPDATE lleva la condicion status="pending" dentro: es la base
    de datos la que decide quien gana, no el codigo. Si primero leyeramos el
    estado y luego escribieramos, los dos caminos podrian leer "pending" a la
    vez y los dos creerian haber ganado.

    Solo se pasa de "pending": una reserva cancelada no revive aunque llegue
    un webhook tardio.

    customer_email llega de Stripe, que lo pide siempre en su checkout. Se
    guarda en el mismo UPDATE para no hacer dos escrituras: el que gana la
    carrera es el unico que lo escribe, y el que pierde no lo pisa.
    """
    result = session.exec(
        update(Booking)
        .where(Booking.id == booking.id)
        .where(Booking.status == "pending")
        .values(status="paid", paid_at=datetime.utcnow(),
                customer_email=customer_email)
    )
    session.commit()

    if result.rowcount != 1:
        return False

    # El objeto en memoria seguia diciendo "pending": hay que releerlo para
    # que quien llama vea el estado nuevo (la plantilla lo usa).
    session.refresh(booking)
    return True

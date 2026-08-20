"""Consultas sobre reservas.

Es el unico puente entre la base de datos y core/booking.py: traduce filas
en el diccionario `taken` que consume la logica de calendario.
"""

from datetime import datetime, timedelta

from sqlmodel import Session, select

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
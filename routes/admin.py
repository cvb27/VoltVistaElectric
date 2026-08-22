"""Agenda de instalaciones para el negocio.

Protegido con HTTP Basic contra una sola contrasena en .env: sin usuarios,
sin sesiones, sin recuperar clave. Es una pagina para dos personas.
"""

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from sqlmodel import Session, select

from core.admin_auth import require_admin
from core.booking import slot_label
from core.export import bookings_csv
from core.templating import templates
from db.booking import get_by_public_id
from db.models import Booking
from db.session import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


def _upcoming(session: Session, state: str, day: date | None = None) -> list[Booking]:
    """Reservas con un estado dado, ordenadas por la cita.

    Con `day` devuelve solo las de ese dia — es la vista del instalador, que
    sale de casa y solo le importa hoy. Sin `day`, de hoy en adelante.
    """
    query = select(Booking).where(Booking.status == state)
    query = (query.where(Booking.service_date == day) if day
             else query.where(Booking.service_date >= date.today()))
    return session.exec(query.order_by(Booking.service_date, Booking.slot)).all()


@router.get("/bookings")
def bookings(request: Request, day: str = "", _: str = Depends(require_admin),
             session: Session = Depends(get_session)):
    """Agenda de instalaciones, en dos listas separadas a proposito.

      confirmed  reservas pagadas. Son las citas reales.
      review     reservas en "pending". Aqui caen DOS casos que la base no
                 puede diferenciar: quien abandono el pago, y quien pago pero
                 cuyo webhook se perdio. Hay que mirarlas en Stripe.

    Sin esa segunda lista, una reserva con el pago colgado no aparece en
    ningun sitio: el cliente ve "We're confirming your payment" y ahi se
    acaba el rastro.
    """
    # ?day=2026-09-15 reduce la agenda a un solo dia. Una fecha mal escrita se
    # ignora en vez de dar error: es un filtro de conveniencia y no merece la
    # pena romper la agenda por un parametro sucio en la URL.
    try:
        picked = date.fromisoformat(day) if day else None
    except ValueError:
        picked = None

    return templates.TemplateResponse("admin/bookings.html", {
        "request": request,
        "confirmed": _upcoming(session, "paid", picked),
        "review": _upcoming(session, "pending", picked),
        "slot_label": slot_label,
        "picked": picked,
        "today": date.today(),
    })


@router.post("/bookings/{public_id}/cancel")
def cancel(public_id: str, _: str = Depends(require_admin),
           session: Session = Depends(get_session)):
    """Cancela una reserva y vuelve a la agenda.

    La fila NO se borra: el deposito ya se cobro y tiene que quedar constancia
    de a quien hay que devolverselo.

    El cupo se libera solo, sin tocar nada mas: taken_map() solo cuenta las
    pagadas y las pendientes recientes, asi que una "cancelled" deja de ocupar
    en cuanto se guarda.
    """
    booking = get_by_public_id(session, public_id)
    if booking:
        booking.status = "cancelled"
        session.add(booking)
        session.commit()
    return RedirectResponse("/admin/bookings", status_code=303)


@router.get("/bookings.csv")
def download_csv(_: str = Depends(require_admin),
                 session: Session = Depends(get_session)):
    """Descarga todas las reservas pagadas, para facturar.

    Sin limite de fecha a proposito: para facturar hacen falta tambien los
    trabajos ya hechos, no solo los que vienen.
    """
    rows = session.exec(
        select(Booking).where(Booking.status == "paid")
        .order_by(Booking.service_date, Booking.slot)
    ).all()
    return Response(
        content=bookings_csv(rows),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bookings.csv"},
    )

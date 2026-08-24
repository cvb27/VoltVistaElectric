"""
Aviso al equipo cuando entra una reserva pagada.

Se apoya en core/emailer.py, que ya existe y ya devuelve False sin romper
cuando no hay SMTP configurado. No agrega ningun servicio ni dependencia.
"""

from core.booking import slot_label
from core.emailer import send_owner_email
from db.models import Booking


def _subject(b: Booking) -> str:
    """Asunto del aviso.

    Lleva fecha, franja y nombre porque en el telefono el asunto es lo unico
    que se ve sin abrir el mensaje: con eso ya se sabe si hay que moverse.
    """
    return f"BOOKING {b.service_date:%a %b %-d} {slot_label(b.slot)} - {b.customer_name}"


def _body(b: Booking) -> str:
    """Cuerpo del aviso: todo lo que hace falta para ir a instalar.

    En texto plano y con las etiquetas alineadas a proposito — se lee igual
    de bien en el movil que en el escritorio, sin depender de HTML.
    """
    return (
        f"NEW BOOKING   #{b.public_id}\n"
        f"{'=' * 44}\n\n"
        f"WHEN     {b.service_date:%A, %B %-d}  -  {slot_label(b.slot)}\n"
        f"WHO      {b.customer_name}  -  {b.customer_phone}\n"
        f"EMAIL    {b.customer_email or '-'}\n"
        f"WHERE    {b.address}\n\n"
        f"PACKAGE  {b.plan_name} - ${b.plan_price}\n"
        # Solo sale la linea si hubo descuento: un "DISCOUNT -$0" en todos los
        # correos seria ruido.
        + (f"DISCOUNT -${b.discount_amount}  ({b.discount_code})\n" if b.discount_amount else "")
        +
        f"PAID     ${b.deposit_amount} deposit\n"
        f"COLLECT  ${b.balance_due} on site\n\n"
        f"NOTES    {b.notes or '-'}\n"
    )


def notify_new_booking(booking: Booking) -> bool:
    """Avisa de una reserva pagada. Devuelve True si el correo salio.

    NUNCA lanza. El cliente ya pago y su pagina de confirmacion tiene que
    cargar aunque el correo falle. La reserva ya esta guardada en la base, asi
    que un aviso perdido no pierde la cita — solo hay que mirar la agenda.
    """
    try:
        return send_owner_email(subject=_subject(booking), body=_body(booking))
    except Exception:
        return False

"""Reserva de instalacion con deposito.

Flujo completo:
    GET  /booking?plan=recommended   el cliente elige fecha y llena datos
    POST /booking/checkout           se valida, se aparta el cupo, va a Stripe
    GET  /booking/confirmed          vuelve de Stripe, se dispara el evento GA4
    POST /booking/webhook            Stripe avisa que el pago se completo
"""

import secrets
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from core.booking import DEPOSIT, BookingUnavailable, open_days, slot_label, validate_selection
from core.checkout import create_booking_session
from core.config import settings
from core.offers import get_plan
from core.templating import templates          # ajustar si tu helper se llama distinto
from db.booking import get_by_stripe_session, taken_map
from db.models import Booking
from db.session import get_session              # ajustar si tu dependencia se llama distinto

router = APIRouter(prefix="/booking", tags=["booking"])


@router.get("")
def choose_date(request: Request, plan: str = "recommended",
                session: Session = Depends(get_session)):
    """Pagina de seleccion de fecha.

    El plan llega como KEY ("recommended"), nunca como precio. El precio
    se resuelve aqui en el servidor con get_plan(). Si llegara como precio
    en la URL, cualquiera podria reservar el plan premium por $1.
    """
    try:
        p = get_plan(plan)
    except (KeyError, ValueError):
        # Plan desconocido: de vuelta a la landing en vez de romper.
        return RedirectResponse("/services/surge-protector-installation", status_code=303)

    return templates.TemplateResponse("booking/select_date.html", {
        "request": request,
        "plan": p,
        "deposit": DEPOSIT,
        "balance": p["price"] - DEPOSIT,
        "days": open_days(taken_map(session)),
    })


@router.post("/checkout")
def start_checkout(request: Request,
                   plan: str = Form(...),
                   service_date: str = Form(...),
                   slot: int = Form(...),
                   customer_name: str = Form(...),
                   customer_phone: str = Form(...),
                   address: str = Form(...),
                   notes: str = Form(""),
                   session: Session = Depends(get_session)):
    """Valida, aparta el cupo y manda a pagar.

    El orden importa: primero validar, despues crear la reserva, y solo
    entonces ir a Stripe. Cobrar antes de validar significaria tener que
    devolver dinero cuando la fecha resulte no estar disponible.
    """
    try:
        p = get_plan(plan)
        day, slot = validate_selection(service_date, slot, taken_map(session))
    except (KeyError, ValueError):
        return RedirectResponse("/services/surge-protector-installation", status_code=303)
    except BookingUnavailable as e:
        # El cupo se lleno o la seleccion no sirve: se vuelve a pintar el
        # calendario ya actualizado, con el mensaje arriba.
        return templates.TemplateResponse("booking/select_date.html", {
            "request": request,
            "plan": p,
            "deposit": DEPOSIT,
            "balance": p["price"] - DEPOSIT,
            "days": open_days(taken_map(session)),
            "error": str(e),
        }, status_code=409)

    # La reserva nace como "pending". Desde este momento su cupo queda
    # apartado durante HOLD_MINUTES, aunque el cliente todavia no pague.
    booking = Booking(
        public_id=secrets.token_urlsafe(8),
        plan_key=p["key"],
        plan_name=p["name"],
        plan_price=p["price"],
        deposit_amount=DEPOSIT,
        balance_due=p["price"] - DEPOSIT,
        service_date=day,
        slot=slot,
        customer_name=customer_name.strip(),
        customer_phone=customer_phone.strip(),
        address=address.strip(),
        notes=notes.strip() or None,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    # {CHECKOUT_SESSION_ID} lo sustituye Stripe por el id real al redirigir.
    stripe_session = create_booking_session(
        amount=DEPOSIT,
        description=f"{p['name']} surge protector — deposit",
        success_url=f"{settings.base_url}/booking/confirmed?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.base_url}/services/surge-protector-installation",
        metadata={"booking_id": booking.public_id},
    )

    booking.stripe_session_id = stripe_session.id
    session.add(booking)
    session.commit()

    return RedirectResponse(stripe_session.url, status_code=303)


@router.get("/confirmed")
def confirmed(request: Request, session_id: str = "",
              session: Session = Depends(get_session)):
    """Pagina de gracias. Aqui se dispara el evento de conversion.

    Trae un respaldo del webhook: si Stripe todavia no lo mando (o fallo),
    se le pregunta directo por el estado del pago. Sin esto, un webhook
    perdido dejaria la reserva en "pending" para siempre.
    """
    booking = get_by_stripe_session(session, session_id) if session_id else None
    if not booking:
        return RedirectResponse("/services/surge-protector-installation", status_code=303)

    if booking.status == "pending":
        try:
            s = stripe.checkout.Session.retrieve(session_id)
            if s.payment_status == "paid":
                booking.status = "paid"
                booking.paid_at = datetime.utcnow()
                session.add(booking)
                session.commit()
        except stripe.error.StripeError:
            pass  # el webhook lo resolvera

    return templates.TemplateResponse("booking/confirmed.html", {
        "request": request,
        "booking": booking,
        "slot_label": slot_label(booking.slot),
    })


@router.post("/webhook")
async def webhook(request: Request, session: Session = Depends(get_session)):
    """Confirmacion de pago del lado de Stripe.

    Es la fuente autoritativa: llega aunque el cliente cierre el navegador
    antes de volver al sitio.

    La firma se verifica siempre. Sin eso, cualquiera podria mandar un POST
    falso a esta URL y marcar reservas como pagadas sin pagar.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return {"ok": False}

    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        booking = get_by_stripe_session(session, data["id"])
        if booking and booking.status == "pending":
            booking.status = "paid"
            booking.paid_at = datetime.utcnow()
            session.add(booking)
            session.commit()

    return {"ok": True}
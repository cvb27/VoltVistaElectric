import stripe
from fastapi import APIRouter, Request, Form, Header, HTTPException
from fastapi.responses import RedirectResponse

from core.config import settings
from core.utils import get_lang
from core.i18n import t
from core.templating import templates
from core.checkout import create_stripe_session

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("")
def pay_page(request: Request):
    lang = get_lang(request)

    stripe_on = bool(settings.stripe_secret_key)  # True si hay key
    paypal_on = bool(settings.paypal_client_id and settings.paypal_client_secret)

    deposit_amount = float(settings.stripe_deposit_amount)
    deposit_amount_fmt = f"${deposit_amount:,.2f}"

    return templates.TemplateResponse(
        "payments.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),

            # flags para el template
            "stripe_on": stripe_on,
            "paypal_on": paypal_on,

            # montos
            "deposit_amount": deposit_amount,
            "deposit_amount_fmt": deposit_amount_fmt,
        },
    )


@router.post("/checkout")
def create_checkout(request: Request, amount: float = Form(...), description: str = Form("")):
    """
    Crea una sesión de pago en Stripe Checkout.
    
    """
    # Validación mínima
    
    try:
        session_url = create_stripe_session(amount, description)
        return RedirectResponse(session_url, status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/success")
def payment_success(request: Request):
    lang = get_lang(request)
    return templates.TemplateResponse(
        "payment_success.html",
        {"request": request, "lang": lang, "t": lambda k: t(lang, k)},
    )

@router.get("/cancel")
def payment_cancel(request: Request):
    lang = get_lang(request)
    stripe_on = bool(settings.stripe_secret_key)

    return templates.TemplateResponse(
        "payments.html",
        {"request": request, 
        "lang": lang,   
        "t": lambda k: t(lang, k),
        "stripe_on": stripe_on,
        }
    )



@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Webhook para confirmar pagos.
    OJO: usa settings.stripe_webhook_secret (minúsculas, según tu config.py).
    """
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.stripe_webhook_secret_payments,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("Payment received:", session.get("amount_total"))

        # TODO: Guardar en SQLite si quieres

    return {"status": "ok"}


@router.post("/link")
def create_shareable_link(request: Request, amount: float = Form(...), description: str = Form("")):
    """
    Genera un link compartible (Stripe Checkout Session URL).
    """
    try:
        session_url = create_stripe_session(amount, description)
        return RedirectResponse(f"/payments/?link={session_url}", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
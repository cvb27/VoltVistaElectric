from fastapi import APIRouter, Request, Depends, Form, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.core.config import settings
from app.core.utils import get_lang, money
from app.core.i18n import t
from app.db.session import get_session
from app.db.models import PaymentRecord
from app.services.stripe_service import stripe_enabled, create_checkout_session, verify_webhook
from app.services.paypal_service import paypal_enabled, create_order, capture_order

router = APIRouter(prefix="/payments", tags=["payments"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def payments_page(request: Request):
    lang = get_lang(request)
    return templates.TemplateResponse(
        "payments.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "stripe_on": stripe_enabled(),
            "paypal_on": paypal_enabled(),
            "deposit_amount": settings.stripe_deposit_amount,
            "deposit_amount_fmt": money(settings.stripe_deposit_amount),
        },
    )


# -------- Stripe --------

@router.post("/stripe/checkout")
def stripe_checkout(
    request: Request,
    purpose: str = Form("deposit"),       # deposit|invoice
    amount: float = Form(0.0),
    email: str = Form(""),
):
    if not stripe_enabled():
        return RedirectResponse(url="/payments?error=stripe_disabled", status_code=303)

    if purpose == "deposit":
        amount = settings.stripe_deposit_amount
    else:
        # pago manual: mínimo de seguridad
        if amount <= 0:
            return RedirectResponse(url="/payments?error=invalid_amount", status_code=303)

    success_url = f"{settings.base_url}/payments/result?status=success&provider=stripe"
    cancel_url = f"{settings.base_url}/payments/result?status=cancel&provider=stripe"

    session = create_checkout_session(
        purpose=purpose,
        amount=float(amount),
        currency=settings.stripe_currency,
        customer_email=email.strip() or None,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return RedirectResponse(url=session.url, status_code=303)


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default=""),
    session_db: Session = Depends(get_session),
):
    if not stripe_enabled():
        return JSONResponse({"ok": False, "reason": "stripe disabled"}, status_code=400)

    payload = await request.body()
    try:
        event = verify_webhook(payload, stripe_signature)
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)

    # Solo guardamos pagos completados
    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]

        purpose = (data.get("metadata") or {}).get("purpose", "invoice")
        amount_total = (data.get("amount_total") or 0) / 100.0
        currency = (data.get("currency") or settings.stripe_currency).lower()
        provider_payment_id = data.get("payment_intent") or data.get("id")

        session_db.add(
            PaymentRecord(
                provider="stripe",
                purpose=purpose,
                amount=float(amount_total),
                currency=currency,
                provider_payment_id=str(provider_payment_id),
                email=data.get("customer_details", {}).get("email"),
                notes="Recorded via Stripe webhook",
            )
        )
        session_db.commit()

    return JSONResponse({"ok": True})


# -------- PayPal --------

@router.post("/paypal/create")
async def paypal_create(
    purpose: str = Form("deposit"),
    amount: float = Form(0.0),
):
    if not paypal_enabled():
        return JSONResponse({"ok": False, "reason": "paypal disabled"}, status_code=400)

    if purpose == "deposit":
        amount = settings.paypal_deposit_amount
    else:
        if amount <= 0:
            return JSONResponse({"ok": False, "reason": "invalid amount"}, status_code=400)

    return_url = f"{settings.base_url}/payments/paypal/return"
    cancel_url = f"{settings.base_url}/payments/result?status=cancel&provider=paypal"

    order = await create_order(purpose, float(amount), settings.paypal_currency, return_url, cancel_url)

    # link de aprobación (payer)
    approve = None
    for link in order.get("links", []):
        if link.get("rel") == "approve":
            approve = link.get("href")
            break

    return {"ok": True, "approve_url": approve, "order_id": order.get("id")}


@router.get("/paypal/return")
async def paypal_return(
    request: Request,
    token: str = "",  # PayPal retorna ?token=ORDER_ID
    session_db: Session = Depends(get_session),
):
    if not paypal_enabled() or not token:
        return RedirectResponse(url="/payments/result?status=cancel&provider=paypal", status_code=303)

    capture = await capture_order(token)

    # Guardar si está COMPLETED
    status = capture.get("status")
    if status == "COMPLETED":
        pu = (capture.get("purchase_units") or [{}])[0]
        payments = (pu.get("payments") or {}).get("captures", [])
        cap0 = payments[0] if payments else {}
        amount_info = cap0.get("amount", {})

        purpose = pu.get("custom_id") or "invoice"
        provider_payment_id = cap0.get("id") or token

        session_db.add(
            PaymentRecord(
                provider="paypal",
                purpose=purpose,
                amount=float(amount_info.get("value", "0") or 0),
                currency=str(amount_info.get("currency_code", settings.paypal_currency)),
                provider_payment_id=str(provider_payment_id),
                notes="Recorded via PayPal capture",
            )
        )
        session_db.commit()

        return RedirectResponse(url="/payments/result?status=success&provider=paypal", status_code=303)

    return RedirectResponse(url="/payments/result?status=cancel&provider=paypal", status_code=303)


@router.get("/result", response_class=HTMLResponse)
def payment_result(request: Request, status: str = "success", provider: str = ""):
    lang = get_lang(request)
    return templates.TemplateResponse(
        "payment_result.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "status": status,
            "provider": provider,
        },
    )

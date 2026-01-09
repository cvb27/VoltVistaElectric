"""
Stripe Checkout (server-side).
- Crea sesión para depósito o pago manual.
- Webhook para confirmar pago y guardarlo en DB.
"""

from typing import Optional
import stripe
from app.core.config import settings

stripe.api_key = settings.stripe_secret_key


def stripe_enabled() -> bool:
    return bool(settings.stripe_secret_key and settings.stripe_webhook_secret)


def create_checkout_session(
    purpose: str,
    amount: float,
    currency: str,
    customer_email: Optional[str],
    success_url: str,
    cancel_url: str,
):
    # Stripe espera monto en centavos
    unit_amount = int(round(amount * 100))

    description = "Deposit" if purpose == "deposit" else "Invoice Payment"

    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=customer_email or None,
        line_items=[
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": f"Voltvista Electric - {description}"},
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"purpose": purpose},
    )
    return session


def verify_webhook(payload: bytes, sig_header: str):
    event = stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig_header,
        secret=settings.stripe_webhook_secret,
    )
    return event

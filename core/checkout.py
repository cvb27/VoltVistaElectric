"""
Lógica de Stripe Checkout — funciones reutilizables.
"""
import stripe
from core.config import settings


def create_stripe_session(amount: float, description: str = "") -> str:
    """
    Crea una sesión de Stripe Checkout.
    
    Args:
        amount: Monto en dólares (ej: 99.99)
        description: Descripción del producto (ej: "Electrical Service Payment")
    
    Returns:
        La URL de la sesión de Stripe (session.url)
    
    Raises:
        ValueError: Si amount <= 0
    """
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": settings.stripe_currency,
                    "product_data": {
                        "name": description.strip() or "Electric Service Payment",
                    },
                    "unit_amount": int(round(amount * 100)),  # Stripe usa centavos
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.base_url}/payments/success",
        cancel_url=f"{settings.base_url}/payments/cancel",
    )
    
    return session.url
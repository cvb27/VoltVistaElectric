"""
Lógica de Stripe Checkout — funciones reutilizables.

Aqui se configura la clave de la API, y no en un router: los dos modulos que
hablan con Stripe (payments y booking) importan este archivo, asi que la clave
queda puesta llegue quien llegue primero. Antes vivia en routes/payments.py y
las reservas solo funcionaban porque main.py lo importaba antes — reordenar
esos imports las habria roto con "No API key provided".
"""
import stripe
from core.config import settings

stripe.api_key = settings.stripe_secret_key


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

def create_booking_session(amount: float, description: str,
                           success_url: str, cancel_url: str, metadata: dict):
    """Sesion de Stripe para una reserva de instalacion.

    Se separa de create_stripe_session porque una reserva necesita tres
    cosas que el cobro suelto no:

      - URLs propias: el cliente vuelve a la pagina de confirmacion de la
        reserva, no a la generica de /payments.
      - metadata: datos propios que Stripe devuelve en el webhook. Ahi va
        el booking_id, que es como el webhook sabe que reserva marcar
        como pagada.
      - El objeto Session completo: hace falta .url para redirigir y .id
        para guardarlo en la reserva y poder buscarla despues.

    Devolver el objeto en vez de la URL es la unica diferencia de forma
    con create_stripe_session, y por eso son dos funciones y no una con
    parametros opcionales: cambiarle el retorno a la existente romperia
    routes/payments.py.
    """
    if amount <= 0:
        raise ValueError("Amount must be greater than 0")

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": settings.stripe_currency,
                "product_data": {"name": description},
                "unit_amount": int(round(amount * 100)),  # Stripe usa centavos
            },
            "quantity": 1,
        }],
        metadata=metadata,
        success_url=success_url,
        cancel_url=cancel_url,
    )
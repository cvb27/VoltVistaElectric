"""
PayPal (Orders v2) minimal:
- create order
- capture order

Se usa httpx y credenciales del .env.
"""

from typing import Optional, Dict
import base64
import httpx
from app.core.config import settings


def paypal_enabled() -> bool:
    return bool(settings.paypal_client_id and settings.paypal_client_secret)


def _base_url() -> str:
    return "https://api-m.sandbox.paypal.com" if settings.paypal_env == "sandbox" else "https://api-m.paypal.com"


def _basic_auth_header() -> str:
    raw = f"{settings.paypal_client_id}:{settings.paypal_client_secret}".encode("utf-8")
    token = base64.b64encode(raw).decode("utf-8")
    return f"Basic {token}"


async def get_access_token() -> str:
    url = f"{_base_url()}/v1/oauth2/token"
    headers = {"Authorization": _basic_auth_header()}
    data = {"grant_type": "client_credentials"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, data=data)
        r.raise_for_status()
        return r.json()["access_token"]


async def create_order(purpose: str, amount: float, currency: str, return_url: str, cancel_url: str) -> Dict:
    token = await get_access_token()
    url = f"{_base_url()}/v2/checkout/orders"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "description": f"Voltvista Electric - {'Deposit' if purpose=='deposit' else 'Invoice Payment'}",
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}",
                },
                "custom_id": purpose,
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        return r.json()


async def capture_order(order_id: str) -> Dict:
    token = await get_access_token()
    url = f"{_base_url()}/v2/checkout/orders/{order_id}/capture"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers)
        r.raise_for_status()
        return r.json()

"""
Utilidades comunes:
- manejo de idioma por query ?lang=es|en (guarda cookie)
- helpers para WhatsApp / SMS links
- formato de montos
"""

from fastapi import Request
from fastapi.responses import Response
from core.config import settings

SUPPORTED_LANGS = {"es", "en"}


def get_lang(request: Request) -> str:
    # 1) query param
    q = (request.query_params.get("lang") or "").lower()
    if q in SUPPORTED_LANGS:
        return q

    # 2) cookie
    c = (request.cookies.get("lang") or "").lower()
    if c in SUPPORTED_LANGS:
        return c

    return settings.default_lang


def persist_lang(response: Response, lang: str) -> None:
    if lang in SUPPORTED_LANGS:
        response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, httponly=False, samesite="lax")


def wa_link(phone: str, message: str) -> str:
    # WhatsApp requires digits; pero lo dejamos flexible (tú pon +1...)
    # Mensaje se URL-encodea en template con |urlencode.
    return f"https://wa.me/{phone.replace('+','').replace(' ','')}"


def sms_link(phone: str, message: str) -> str:
    # En muchos móviles: sms:+1...&body=...
    return f"sms:{phone}"


def money(amount: float) -> str:
    return f"{amount:,.2f}"

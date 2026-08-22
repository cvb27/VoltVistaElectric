"""
Centraliza configuración de la app desde variables de entorno.

- Mantener aquí TODAS las variables .env evita "magia" y facilita deploy.
- Un junior puede encontrar y editar settings rápidamente.
"""

from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    # App
    app_name: str = _get("APP_NAME", "Voltvista Electric")
    base_url: str = _get("BASE_URL", "http://127.0.0.1:8000")
    default_lang: str = _get("DEFAULT_LANG", "en")

    # Business
    phone: str = _get("BUSINESS_PHONE", "")
    sms: str = _get("BUSINESS_SMS", "")
    whatsapp: str = _get("BUSINESS_WHATSAPP", "")
    email: str = _get("BUSINESS_EMAIL", "")
    city: str = _get("BUSINESS_CITY", "")
    service_area: str = _get("BUSINESS_SERVICE_AREA", "")
    instagram_url: str = _get("INSTAGRAM_URL", "")

    # Business identity — usado en JSON-LD, footer y Google Ads.
    # Centralizado aquí para que NAP sea idéntico en todo el sitio.
    business_name: str = _get("BUSINESS_NAME", "VoltVistaElectric")
    address: str = _get("BUSINESS_ADDRESS", "")
    state: str = _get("BUSINESS_STATE", "FL")
    zip_code: str = _get("BUSINESS_ZIP", "")
    lat: float = float(_get("BUSINESS_LAT") or "28.392484")
    lng: float = float(_get("BUSINESS_LNG") or "-81.506867")
    hours: str = _get("BUSINESS_HOURS", "Mo-Fr 08:00-18:00")
    business_url: str = _get("BUSINESS_URL", "https://voltvistaelectric.com")
    logo_url: str = _get("BUSINESS_LOGO_URL", "https://voltvistaelectric.com/static/img/logo.png")

    # Tracking IDs — se rellenan vía .env, nunca hardcodeados.
    ga4_id: str = _get("GA4_ID", "")
    gads_id: str = _get("GADS_ID", "")
    # Etiqueta de la accion de conversion de Ads: la parte tras la barra en
    # "AW-123456789/AbC-D_efGhIjK". Vacia = no se emite la conversion.
    gads_conversion_label: str = _get("GADS_CONVERSION_LABEL", "")

    # Postgres
    database_url: str = _get("DATABASE_URL", "sqlite:///./voltvista.db")

    # Email (optional)
    smtp_host: str = _get("SMTP_HOST", "")
    smtp_port: int = int(_get("SMTP_PORT", "587") or "587")
    smtp_user: str = _get("SMTP_USER", "")
    smtp_pass: str = _get("SMTP_PASS", "")
    email_to_owner: str = _get("EMAIL_TO_OWNER", "")

    # Stripe
    stripe_secret_key: str = _get("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret_payments: str = _get("STRIPE_WEBHOOK_SECRET_PAYMENTS", "")
    stripe_webhook_secret_booking: str = _get("STRIPE_WEBHOOK_SECRET_BOOKING", "")
    stripe_currency: str = _get("STRIPE_CURRENCY", "usd")
    stripe_deposit_amount: float = float(_get("STRIPE_DEPOSIT_AMOUNT", "99.00"))

    # Booking
    # El depósito vive en .env, no en el código: así bajarlo para probar no
    # deja un valor de prueba dentro de un commit — que es justo lo que pasó.
    booking_deposit: int = int(_get("BOOKING_DEPOSIT", "50"))

    # Admin
    # Vacía = /admin queda cerrado. Un despliegue sin esta variable no expone
    # la agenda por accidente.
    admin_password: str = _get("ADMIN_PASSWORD", "")

    # PayPal
    paypal_client_id: str = _get("PAYPAL_CLIENT_ID", "")
    paypal_client_secret: str = _get("PAYPAL_CLIENT_SECRET", "")
    paypal_env: str = _get("PAYPAL_ENV", "sandbox")  # sandbox|live
    paypal_deposit_amount: float = float(_get("PAYPAL_DEPOSIT_AMOUNT", "99.00"))
    paypal_currency: str = _get("PAYPAL_CURRENCY", "USD")

    # Upload rules
    max_upload_mb: int = int(_get("MAX_UPLOAD_MB", "8") or "8")


settings = Settings()

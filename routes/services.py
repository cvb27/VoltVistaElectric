"""
Landings SEO por servicio (panel upgrade, installations, emergency).

Una ruta y template por servicio para captar keywords long-tail locales.
Cada landing inyecta su propio JSON-LD Service vía build_service_schema.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.config import settings
from core.i18n import t
from core.seo import build_service_schema
from core.templating import templates
from core.utils import get_lang

router = APIRouter(prefix="/services", tags=["services"])


def _service_context(request: Request, service_name: str, url_path: str, description: str) -> dict:
    """Construye el contexto compartido de una landing de servicio.
    Recibe request, nombre del servicio, sub-path y descripción para el schema.
    Devuelve dict con todas las variables que el template necesita."""
    lang = get_lang(request)
    service_url = f"{settings.business_url}{url_path}"
    return {
        "request": request,
        "lang": lang,
        "t": lambda k: t(lang, k),
        "app_name": settings.app_name,
        "phone": settings.phone,
        "whatsapp": settings.whatsapp,
        "areas": [a.strip() for a in settings.service_area.split(",") if a.strip()],
        "service_jsonld": build_service_schema(settings, service_name, service_url, description),
    }


@router.get("/panel-upgrade", response_class=HTMLResponse)
async def panel_upgrade(request: Request):
    """Landing SEO para actualización de panel eléctrico."""
    ctx = _service_context(request, "Electrical Panel Upgrade", "/services/panel-upgrade",
                           "Expert panel upgrades in Orlando, FL by VoltVista Electric.")
    return templates.TemplateResponse("services/panel_upgrade.html", ctx)


@router.get("/electrical-installations", response_class=HTMLResponse)
async def electrical_installations(request: Request):
    """Landing SEO para instalaciones eléctricas residenciales y comerciales."""
    ctx = _service_context(request, "Electrical Installations", "/services/electrical-installations",
                           "Residential and commercial electrical installations in Orlando, FL.")
    return templates.TemplateResponse("services/electrical_installations.html", ctx)


@router.get("/ev-charger-installation", response_class=HTMLResponse)
async def ev_charger_installation(request: Request):
    """Landing SEO para instalación de cargadores EV."""
    ctx = _service_context(
        request,
        "EV Charger Installation",
        "/services/ev-charger-installation",
        "Professional EV charger installation in Orlando, FL. "
        "VoltVista Electric — 10+ years experience, fully insured."
    )
    return templates.TemplateResponse("services/ev_charger_installation.html", ctx)

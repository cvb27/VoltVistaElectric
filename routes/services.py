"""
Landings SEO por servicio .

Una ruta y template por servicio para captar keywords long-tail locales.
Cada landing inyecta su propio JSON-LD Service vía build_service_schema.

Las URLs retiradas se mantienen como redirects 301 para no perder el
posicionamiento que ya acumularon: panel-upgrade y electrical-installations van
a la pagina de reparaciones; surge-protector y ev-charger, a la de iluminacion,
que es la linea de negocio que las reemplaza.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

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


# ---------------------------------------------------------------------------
# Servicios activos
# ---------------------------------------------------------------------------

@router.get("/electrical-repair-installation", response_class=HTMLResponse)
async def electrical_repair_installation(request: Request):
    """Landing de reparaciones e instalaciones electricas.
    Reemplaza a las antiguas panel-upgrade y electrical-installations."""
    ctx = _service_context(
        request,
        "Electrical Repair and Installation",
        "/services/electrical-repair-installation",
        "Professional electrical repair and installation services in Orlando, FL.",
    )
    return templates.TemplateResponse("services/electrical_repair_installation.html", ctx)


# ---------------------------------------------------------------------------
# URLs retiradas — redirect 301 permanente
#
# Estas paginas ya no existen, pero estuvieron en el sitemap y pueden estar
# indexadas o enlazadas desde afuera. El 301 traspasa esa autoridad a la pagina
# nueva en vez de devolver 404. No borrar sin revisar Search Console primero.
# ---------------------------------------------------------------------------

# Destinos de las redirecciones, uno por familia. Constantes y no literales
# sueltos para que, si una pagina de reemplazo cambia de URL, solo haya que
# tocar una linea.
_REPLACEMENT = "/services/electrical-repair-installation"
_LIGHTING = "/services/lighting-installation"


@router.get("/panel-upgrade")
async def panel_upgrade_redirect():
    """301 permanente a la pagina que la reemplazo.

    Antes intentaba renderizar services/panel_upgrade.html, que fue borrada, y
    devolvia 500. Lo recibian tanto Google como quien llegaba desde el post
    panel-upgrade-orlando.md, que sigue enlazando esta URL.
    """
    return RedirectResponse(_REPLACEMENT, status_code=301)


@router.get("/electrical-installations")
async def electrical_installations_redirect():
    """301 permanente a la pagina que la reemplazo. Mismo caso que la de arriba."""
    return RedirectResponse(_REPLACEMENT, status_code=301)


@router.get("/surge-protector-installation")
async def surge_protector_redirect():
    """301 a iluminacion. La oferta de surge se retiro en septiembre de 2026.

    Fue el destino de la campana de Google Ads, asi que es la URL retirada con
    mas enlaces entrantes: el 301 es lo unico que evita perderlos."""
    return RedirectResponse(_LIGHTING, status_code=301)


@router.get("/ev-charger-installation")
async def ev_charger_redirect():
    """301 a iluminacion. Retirada junto con la de surge, mismo motivo."""
    return RedirectResponse(_LIGHTING, status_code=301)

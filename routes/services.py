"""
Landings SEO por servicio .

Una ruta y template por servicio para captar keywords long-tail locales.
Cada landing inyecta su propio JSON-LD Service vía build_service_schema.

Las URLs retiradas (panel-upgrade, electrical-installations) se mantienen como
redirects 301 para no perder el posicionamiento que ya acumularon.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.config import settings
from core.i18n import t
from core.offers import load_offers
from core.seo import build_service_schema
from core.templating import templates
from core.utils import get_lang
from core.booking import DEPOSIT

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


@router.get("/surge-protector-installation", response_class=HTMLResponse)
async def surge_protector_installation(request: Request):
    """Landing de surge protector. Es el destino de la campana de Google Ads.

    Los tres planes y sus precios salen de data/surge_offers.json — se editan ahi,
    sin tocar codigo. El mismo JSON alimenta el bloque de precios del template y
    las Offer del JSON-LD, asi que nunca se pueden desincronizar entre si."""
    ctx = _service_context(
        request,
        "Surge Protector Installation",
        "/services/surge-protector-installation",
        "Whole-home surge protector installation in Orlando, FL. "
        "Protect your appliances and electronics from power surges.",
    )

    offers = load_offers()
    ctx["plans"] = offers["plans"]
    ctx["from_price"] = offers["from_price"]
    ctx["deposit"] = DEPOSIT

    # Precios en el JSON-LD: habilita que Google muestre el rango en resultados.
    ctx["service_jsonld"]["offers"] = [
        {
            "@type": "Offer",
            "name": p["name"],
            "price": p["price"],
            "priceCurrency": "USD",
        }
        for p in offers["plans"]
    ]

    return templates.TemplateResponse("services/surge_protector_installation.html", ctx)


@router.get("/ev-charger-installation", response_class=HTMLResponse)
async def ev_charger_installation(request: Request):
    """Landing de instalacion de cargadores EV."""
    ctx = _service_context(
        request,
        "EV Charger Installation",
        "/services/ev-charger-installation",
        "Professional EV charger installation in Orlando, FL. "
        "VoltVista Electric — 10+ years experience, fully insured.",
    )
    return templates.TemplateResponse("services/ev_charger_installation.html", ctx)


# ---------------------------------------------------------------------------
# URLs retiradas — redirect 301 permanente
#
# Estas dos paginas ya no existen, pero estuvieron en el sitemap y pueden estar
# indexadas o enlazadas desde afuera. El 301 traspasa esa autoridad a la pagina
# nueva en vez de devolver 404. No borrar sin revisar Search Console primero.
# ---------------------------------------------------------------------------

# Destino de las dos redirecciones. Una sola constante para que, si la pagina
# de reemplazo cambia de URL, no haya que acordarse de tocar dos sitios.
_REPLACEMENT = "/services/electrical-repair-installation"


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


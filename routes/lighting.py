"""
Paginas de iluminacion: el hub /services/lighting-installation y una pagina
hija por servicio en /services/{slug}.

Todo sale de data/lighting_services.json via core/lighting.py: anadir un
servicio no toca ni este archivo ni las plantillas.

Las URLs retiradas de la linea electrica (panel-upgrade, etc.) viven como 301
en routes/services.py. Ese router se monta antes que este en main.py, asi que
sus rutas fijas ganan a la ruta /{slug} de abajo.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.config import settings
from core.lighting import get_service, hero_slides, load_services
from core.seo import parse_areas
from core.seo_services import build_service_list_schema, build_service_page_schema
from core.templating import templates

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/lighting-installation", response_class=HTMLResponse)
# Hub de iluminacion: indice con una tarjeta por servicio publicado
async def lighting_installation(request: Request):
    """Hub de iluminacion. Solo resume: el desarrollo vive en cada hija."""
    services = load_services()
    return templates.TemplateResponse(
        "services/lighting_installation.html",
        {
            "request": request,
            "services": services,
            "areas": parse_areas(settings.service_area),
            "jsonld": build_service_list_schema(settings, services),
        },
    )


@router.get("/{slug}", response_class=HTMLResponse)
# Pagina hija de un servicio de iluminacion (roofline, landscape, relamping...)
async def lighting_service(request: Request, slug: str):
    """Pagina de un servicio publicado; 404 si el slug no existe o es borrador.

    El 404 tambien cubre los borradores a proposito: una pagina con
    [PLACEHOLDER] no debe poder abrirse aunque alguien adivine la URL.
    """
    service = get_service(slug)
    if service is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "services/service_page.html",
        {
            "request": request,
            "service": service,
            "hero_slides": hero_slides(service),
            "areas": parse_areas(settings.service_area),
            "jsonld": build_service_page_schema(settings, service),
        },
    )

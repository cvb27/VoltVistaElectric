"""
Paginas por zona: /areas/{slug} (por ejemplo /areas/dr-phillips).

Todo sale de data/areas.json via core/areas.py: anadir una zona no toca ni
este archivo ni la plantilla.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.areas import get_area
from core.config import settings
from core.lighting import load_services
from core.seo_services import build_area_page_schema
from core.templating import templates

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("/{slug}", response_class=HTMLResponse)
# Pagina de una zona de servicio (Dr. Phillips, Windermere...)
async def area_page(request: Request, slug: str):
    """Pagina de una zona publicada; 404 si no existe o es borrador.

    `services` (slug -> servicio) da el nombre del enlace de cada trabajo.
    """
    area = get_area(slug)
    if area is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "areas/area_page.html",
        {
            "request": request,
            "area": area,
            "services": {s["slug"]: s for s in load_services()},
            "jsonld": build_area_page_schema(settings, area),
        },
    )

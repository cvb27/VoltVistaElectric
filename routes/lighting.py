"""
Hub de servicios de iluminacion: /services/lighting-installation.

Va en su propio router y no dentro de routes/services.py porque ese archivo ya
esta en 135 lineas, por encima del limite de 120 de CLAUDE.md 4.1, y anadirle
una ruta mas lo empeoraria. La alternativa que prescribe CLAUDE.md — sacar su
_service_context a core/ — obligaria a tocar las rutas de surge, EV y repair,
que esta tarea deja explicitamente fuera de alcance.

Los servicios que se muestran salen de data/lighting_services.json via
core/lighting.py: anadir uno nuevo no toca ni esta ruta ni la plantilla.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.config import settings
from core.lighting import load_lighting
from core.templating import templates

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/lighting-installation", response_class=HTMLResponse)
async def lighting_installation(request: Request):
    """Landing hub de iluminacion: roofline permanente y landscape.

    Los modulos de servicio se pintan iterando sobre la lista del JSON, asi que
    la pagina crece a tres o cuatro servicios sin escribir HTML nuevo.
    """
    data = load_lighting()
    return templates.TemplateResponse(
        "services/lighting_installation.html",
        {
            "request": request,
            "services": data["services"],
            "gallery": data["gallery"],
            # areas se arma igual que en routes/services.py: la cadena de .env
            # separada por comas se convierte en lista para pintar los badges.
            "areas": [a.strip() for a in settings.service_area.split(",") if a.strip()],
        },
    )

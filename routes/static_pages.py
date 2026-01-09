"""
Páginas estáticas (pero útiles) para el MVP:

- /emergency  : página de emergencias con disclaimer + CTAs
- /reviews    : página de reseñas/testimonios (cargadas desde data/reviews.json)

Nota:
- Usamos Jinja2 templates que ya tienes: emergency.html y reviews.html
- Si aún no existen esos templates, dímelo y te los genero.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.utils import get_lang
from core.i18n import t
from services.reviews import load_reviews

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/emergency", response_class=HTMLResponse)
def emergency_page(request: Request):
    """
    Página simple de "Servicios de emergencia" con disclaimer.
    Ideal para SEO local y para convertir urgencias en leads.
    """
    lang = get_lang(request)

    return templates.TemplateResponse(
        "emergency.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "phone": settings.phone,
            "whatsapp": settings.whatsapp,
            "city": settings.city,
        },
    )


@router.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request):
    """
    Página de reseñas. Las reseñas se administran sin panel vía JSON:
    data/reviews.json
    """
    lang = get_lang(request)
    reviews = load_reviews()

    return templates.TemplateResponse(
        "reviews.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "city": settings.city,
            "reviews": reviews,
        },
    )

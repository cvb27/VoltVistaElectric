from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.utils import get_lang
from core.i18n import t
from core.config import settings
from core.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Renderiza la landing principal con hero video + 5 secciones."""
    lang = get_lang(request)
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
        },
    )

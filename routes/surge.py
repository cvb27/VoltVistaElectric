from fastapi import APIRouter, Request

from core.config import settings
from core.offers import load_offers
from core.templating import templates
from core.utils import get_lang

router = APIRouter(prefix="/surge-protector", tags=["surge"])


@router.get("")
def surge_landing(request: Request):
    data = load_offers()
    return templates.TemplateResponse(
        "surge_landing.html",
        {
            "request": request,
            "lang": get_lang(request),
            "plans": data["plans"],
            "from_price": data["from_price"],
            "phone": settings.phone,
        },
    )
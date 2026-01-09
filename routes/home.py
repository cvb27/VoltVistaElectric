from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.utils import get_lang
from core.i18n import t
from core.config import settings
from services.gallery import load_gallery
from services.products import load_products
from services.clients import load_clients, split_highlights
from services.reviews import load_reviews

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    lang = get_lang(request)

    gallery = load_gallery()
    products = load_products()
    clients = load_clients()
    highlights, others = split_highlights(clients)
    reviews = load_reviews()

    # Servicios placeholder (edítalos en un solo lugar)
    services = [
        "Troubleshooting / Diagnostics",
        "Outlet & Switch Replacement",
        "GFCI Installation & Repair",
        "Lighting (Indoor/Outdoor)",
        "Panel Upgrades (as permitted)",
        "EV Charger Prep / Dedicated Circuits",
    ]

    # Áreas placeholder
    areas = [a.strip() for a in settings.service_area.split(",") if a.strip()]

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),

            "app_name": settings.app_name,
            "city": settings.city,
            "instagram_url": settings.instagram_url,

            "phone": settings.phone,
            "sms": settings.sms,
            "whatsapp": settings.whatsapp,
            "services": services,
            "areas": areas,

            "gallery": gallery[:12],
            "products": products[:8],
            "client_highlights": highlights[:8],
            "reviews": reviews[:6],
        },
    )

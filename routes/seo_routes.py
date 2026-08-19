from fastapi import APIRouter, Response, Request
from core.config import settings
from core.templating import templates
from core.utils import get_lang

router = APIRouter(tags=["seo"])


@router.get("/robots.txt")
def robots():
    # Simple y seguro para MVP
    txt = f"""User-agent: *
Allow: /

Sitemap: {settings.base_url}/sitemap.xml
"""
    return Response(content=txt, media_type="text/plain")


@router.get("/services/electrical-repair-installation")
def electrical_repair_installation(request: Request):
    lang = get_lang(request)
    areas = ["Lake Buena Vista", "Dr. Phillips", "Windermere", "Winter Garden", "Celebration"]

    service_jsonld = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Electrical Repair and Installation",
        "provider": {
            "@type": "LocalBusiness",
            "name": "VoltVista Electric",
            "url": settings.business_url,
            "areaServed": areas,
        },
        "description": "Professional electrical repair and installation services in Orlando, FL",
        "image": f"{settings.business_url}/static/img/logo.png",
    }
    
    return templates.TemplateResponse(
        "services/electrical-repair-installation.html",
        {
            "request": request,
            "lang": lang,
            "areas": areas,
            "phone": settings.phone,
            "service_jsonld": service_jsonld
        },
    )

@router.get("/services/surge-protector-installation")
def surge_protector_installation(request: Request):
    lang = get_lang(request)
    areas = ["Lake Buena Vista", "Dr. Phillips", "Windermere", "Winter Garden", "Celebration"]

    service_jsonld = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Surge Protector Installation",
        "provider": {
            "@type": "LocalBusiness",
            "name": "VoltVista Electric",
            "url": settings.business_url,
            "areaServed": areas,
        },
        "description": "Professional whole-home surge protector installation in Orlando, FL. Protect your home from power surges.",
        "image": f"{settings.business_url}/static/img/logo.png",
    }
    
    return templates.TemplateResponse(
        "services/surge-protector-installation.html",
        {
            "request": request,
            "lang": lang,
            "areas": areas,
            "phone": settings.phone,
            "service_jsonld": service_jsonld
        },
    )


@router.get("/sitemap.xml")
def sitemap():
    # MVP: lista de páginas fijas (puedes extender con blog dinámico)
    urls = [
        f"{settings.base_url}/",
        f"{settings.base_url}/estimate",
        f"{settings.base_url}/payments",
        f"{settings.base_url}/blog",
        f"{settings.base_url}/services/panel-upgrade",
        f"{settings.base_url}/services/electrical-installations",
        f"{settings.base_url}/services/ev-charger-installation",
        f"{settings.base_url}/blog/panel-upgrade-orlando",
        f"{settings.base_url}/blog/ev-charger-installation-orlando",
        f"{settings.base_url}/blog/electrical-problems-orlando-homes",
    ]

    xml_items = "\n".join([f"<url><loc>{u}</loc></url>" for u in urls])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_items}
</urlset>
"""
    return Response(content=xml, media_type="application/xml")

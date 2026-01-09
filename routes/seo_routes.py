from fastapi import APIRouter, Response
from core.config import settings

router = APIRouter(tags=["seo"])


@router.get("/robots.txt")
def robots():
    # Simple y seguro para MVP
    txt = f"""User-agent: *
Allow: /

Sitemap: {settings.base_url}/sitemap.xml
"""
    return Response(content=txt, media_type="text/plain")


@router.get("/sitemap.xml")
def sitemap():
    # MVP: lista de páginas fijas (puedes extender con blog dinámico)
    urls = [
        f"{settings.base_url}/",
        f"{settings.base_url}/estimate",
        f"{settings.base_url}/payments",
        f"{settings.base_url}/reviews",
        f"{settings.base_url}/emergency",
        f"{settings.base_url}/blog",
    ]

    xml_items = "\n".join([f"<url><loc>{u}</loc></url>" for u in urls])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_items}
</urlset>
"""
    return Response(content=xml, media_type="application/xml")

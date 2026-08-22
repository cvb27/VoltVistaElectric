"""
Archivos para rastreadores: robots.txt y sitemap.xml.

Las paginas de servicio NO viven aqui — estan en routes/services.py.
Este archivo solo genera los dos archivos que leen los bots.

Al agregar o quitar una pagina del sitio, actualizar la lista de urls de abajo.
"""

from fastapi import APIRouter, Response
from core.config import settings


router = APIRouter(tags=["seo"])


@router.get("/robots.txt")
def robots():
    """robots.txt minimo: permite todo y apunta al sitemap."""
    txt = f"""User-agent: *
Allow: /
Disallow: /admin

Sitemap: {settings.base_url}/sitemap.xml
"""
    return Response(content=txt, media_type="text/plain")


@router.get("/sitemap.xml")
def sitemap():
    """Sitemap con lista fija de paginas.

    No incluir aqui URLs retiradas (panel-upgrade, electrical-installations):
    responden 301 y no deben ofrecerse a Google como destino."""

    urls = [
        f"{settings.base_url}/",
        f"{settings.base_url}/estimate",
        f"{settings.base_url}/payments",
        f"{settings.base_url}/blog",
        f"{settings.base_url}/services/electrical-repair-installation",
        f"{settings.base_url}/services/surge-protector-installation",
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

"""
Archivos para rastreadores: robots.txt y sitemap.xml.

Las paginas de servicio NO viven aqui — estan en routes/services.py.
Este archivo solo genera los dos archivos que leen los bots.
"""

from fastapi import APIRouter, Response

from core.config import settings
from core.posts import load_posts

router = APIRouter(tags=["seo"])

# Paginas fijas del sitio. Al crear una pagina nueva se anade aqui.
#
# Los posts del blog NO van en esta lista: se generan leyendo el mismo indice
# que usa /blog, asi que publicar uno nuevo lo mete en el sitemap sin tocar
# este archivo. Antes estaban escritos a mano y era facil olvidarse.
_STATIC_PATHS = [
    "/",
    "/estimate",
    "/payments",
    "/blog",
    "/services/electrical-repair-installation",
    "/services/surge-protector-installation",
    "/services/ev-charger-installation",
]


def _url(path: str, lastmod: str = "") -> str:
    """Una entrada <url> del sitemap. El <lastmod> solo si se conoce de verdad."""
    mod = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    return f"<url><loc>{settings.base_url}{path}</loc>{mod}</url>"


@router.get("/robots.txt")
def robots():
    """robots.txt minimo: permite todo menos /admin y apunta al sitemap."""
    txt = f"""User-agent: *
Allow: /
Disallow: /admin

Sitemap: {settings.base_url}/sitemap.xml
"""
    return Response(content=txt, media_type="text/plain")


@router.get("/sitemap.xml")
def sitemap():
    """Sitemap del sitio: paginas fijas + posts del blog.

    Las paginas fijas no llevan <lastmod>: no guardamos cuando cambiaron, y
    una fecha inventada es peor que ninguna — Google deja de fiarse del campo
    si no coincide con la realidad. Los posts si lo llevan, porque su fecha
    real esta en el indice.

    Las URLs retiradas (panel-upgrade, electrical-installations) responden 301
    y por eso no se ofrecen aqui como destino.
    """
    entries = [_url(p) for p in _STATIC_PATHS]
    entries += [_url(f"/blog/{p['slug']}", p.get("published_at", ""))
                for p in load_posts()]

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(entries) + "\n</urlset>\n")
    return Response(content=xml, media_type="application/xml")

"""
Archivos que bots y navegadores piden en una URL fija de la raiz:
robots.txt, sitemap.xml, favicon.ico y site.webmanifest.

Las paginas de servicio NO viven aqui — estan en routes/services.py.
"""

from pathlib import Path

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings
from core.posts import load_posts

router = APIRouter(tags=["seo"])

_ICONS = Path(__file__).resolve().parent.parent / "static" / "icons"

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
    "/services/lighting-installation",
    "/services/electrical-repair-installation",
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

    Las URLs retiradas (panel-upgrade, electrical-installations,
    surge-protector-installation, ev-charger-installation) responden 301 y por
    eso no se ofrecen aqui como destino.
    """
    entries = [_url(p) for p in _STATIC_PATHS]
    entries += [_url(f"/blog/{p['slug']}", p.get("published_at", ""))
                for p in load_posts()]

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(entries) + "\n</urlset>\n")
    return Response(content=xml, media_type="application/xml")



@router.get("/favicon.ico", include_in_schema=False)
def favicon():
    """El mismo favicon.ico de static/icons, servido en la raiz.

    base.html ya lo declara con <link rel="icon">, pero los navegadores y el
    rastreador de favicons de Google piden /favicon.ico por su cuenta; sin esta
    ruta recibian un 404 y mostraban el globo generico."""
    return FileResponse(_ICONS / "favicon.ico", media_type="image/x-icon")


@router.get("/site.webmanifest", include_in_schema=False)
def webmanifest():
    """Manifest para "Anadir a pantalla de inicio" en Android.

    Es una ruta y no un .json estatico para que el nombre salga de .env (no se
    hardcodea, CLAUDE.md 2) y los iconos lleven el mismo ?v= que el resto.
    Sin theme_color ni background_color: el JSON no puede leer palette.css y
    un hex suelto aqui se desincronizaria de la paleta. Android usa blanco."""
    v = settings.asset_version
    return JSONResponse({
        "name": settings.business_name,
        # Android corta a ~12 caracteres bajo el icono: solo la primera palabra.
        "short_name": settings.business_name.split()[0],
        "start_url": "/",
        "display": "browser",
        "icons": [
            {"src": f"/static/icons/icon-192.png?v={v}", "sizes": "192x192", "type": "image/png"},
            {"src": f"/static/icons/icon-512.png?v={v}", "sizes": "512x512", "type": "image/png"},
        ],
    }, media_type="application/manifest+json")

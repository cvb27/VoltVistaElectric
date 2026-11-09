"""
URLs retiradas de /services/ — todas responden 301 permanente al hub de
iluminacion. Las paginas de servicio activas viven en routes/lighting.py.

Estas paginas ya no existen, pero estuvieron en el sitemap y pueden estar
indexadas o enlazadas desde afuera. El 301 traspasa esa autoridad a la pagina
nueva en vez de devolver 404. No borrar sin revisar Search Console primero.

Todas apuntan DIRECTO al hub, sin cadenas: un 301 que lleva a otro 301 pierde
autoridad en cada salto y Google deja de seguirlo pasado cierto numero.
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/services", tags=["services"])

# Destino unico de todas las redirecciones. Constante y no literal suelto para
# que, si el hub cambia de URL, solo haya que tocar una linea.
_LIGHTING = "/services/lighting-installation"


@router.get("/electrical-repair-installation")
# 301: la linea de servicios electricos se retiro en noviembre de 2026
async def electrical_repair_redirect():
    """Fue la landing de reparaciones e instalaciones electricas, enlazada
    desde el home y el footer. Su trafico va ahora al hub de iluminacion."""
    return RedirectResponse(_LIGHTING, status_code=301)


@router.get("/panel-upgrade")
# 301: pagina retirada; la sigue enlazando la version vieja del post de paneles
async def panel_upgrade_redirect():
    """Antes redirigia a electrical-repair-installation; ahora va directo al
    hub para no encadenar dos 301."""
    return RedirectResponse(_LIGHTING, status_code=301)


@router.get("/electrical-installations")
# 301: pagina retirada, mismo caso que panel-upgrade
async def electrical_installations_redirect():
    """301 directo al hub. Mismo caso que la de arriba."""
    return RedirectResponse(_LIGHTING, status_code=301)


@router.get("/surge-protector-installation")
# 301: la oferta de surge se retiro en septiembre de 2026
async def surge_protector_redirect():
    """Fue el destino de la campana de Google Ads, asi que es la URL retirada
    con mas enlaces entrantes: el 301 es lo unico que evita perderlos."""
    return RedirectResponse(_LIGHTING, status_code=301)


@router.get("/ev-charger-installation")
# 301: retirada junto con la de surge, mismo motivo
async def ev_charger_redirect():
    """301 directo al hub de iluminacion."""
    return RedirectResponse(_LIGHTING, status_code=301)

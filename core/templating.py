"""
Instancia compartida de Jinja2Templates con variables SEO inyectadas globalmente.

Todas las rutas importan este singleton para que `global_jsonld` y `business_url`
estén disponibles en cualquier plantilla sin pasarlos en cada TemplateResponse.
"""

from fastapi.templating import Jinja2Templates

from core.config import settings
from core.seo import build_local_business_schema


def _build_templates() -> Jinja2Templates:
    """Construye la instancia única de Jinja2Templates con globals SEO.
    Recibe nada (lee el singleton settings de core.config).
    Devuelve Jinja2Templates lista para usar en todas las rutas."""
    tpl = Jinja2Templates(directory="templates")
    tpl.env.globals["global_jsonld"] = build_local_business_schema(settings)
    tpl.env.globals["business_url"] = settings.business_url
    tpl.env.globals["settings"] = settings
    return tpl


templates = _build_templates()

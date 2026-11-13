"""
JSON-LD de las paginas de iluminacion (ItemList para el hub y Service para
cada pagina hija) y de las paginas por zona (Service acotado a la zona).

Separado de core/seo.py por el limite de 120 lineas (CLAUDE.md 4.1). Mismas
reglas: funciones puras que reciben datos y devuelven un dict.
"""

from core.seo import parse_areas


def _base(cfg) -> str:
    """URL del sitio sin barra final, para concatenar rutas sin dobles //."""
    return cfg.business_url.rstrip("/")


def _service_url(cfg, service: dict) -> str:
    """URL absoluta de la pagina hija de un servicio."""
    return f"{_base(cfg)}/services/{service['slug']}"


def build_service_page_schema(cfg, service: dict) -> dict:
    """Schema Service de una pagina hija.

    Recibe cfg (settings) y la entrada del servicio de lighting_services.json.
    El provider apunta por @id al LocalBusiness global de base.html en vez de
    repetirlo: asi Google entiende que es el mismo negocio y no otro.
    """
    url = _service_url(cfg, service)
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "@id": f"{url}#service",
        "name": service["h1"],
        "serviceType": service["h1"],
        "description": service["meta_description"],
        "url": url,
        "provider": {"@id": f"{_base(cfg)}/#business"},
        "areaServed": [{"@type": "Place", "name": a} for a in parse_areas(cfg.service_area)],
    }


def build_service_list_schema(cfg, services: list[dict]) -> dict:
    """Schema ItemList del hub: un elemento por servicio publicado, en orden.

    Recibe cfg (settings) y la lista que devuelve core.lighting.load_services().
    """
    items = [
        {
            "@type": "ListItem",
            # schema.org cuenta las posiciones desde 1, no desde 0.
            "position": i + 1,
            "name": s["h1"],
            "url": _service_url(cfg, s),
        }
        for i, s in enumerate(services)
    ]
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Lighting Services",
        "itemListElement": items,
    }


def build_area_page_schema(cfg, area: dict) -> dict:
    """Schema Service de una pagina de zona (/areas/{slug}).

    Recibe cfg (settings) y la entrada de data/areas.json. Es un Service y no
    un segundo LocalBusiness: eso le diria a Google que hay una sede en la
    zona, y el negocio esta en otro sitio. areaServed lleva el mismo nombre
    que la lista de .env para que coincida con el del LocalBusiness global.
    """
    url = f"{_base(cfg)}/areas/{area['slug']}"
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "@id": f"{url}#service",
        "name": area["h1"],
        "serviceType": "Lighting Installation",
        "description": area["meta_description"],
        "url": url,
        "provider": {"@id": f"{_base(cfg)}/#business"},
        "areaServed": {"@type": "Place", "name": area["name"]},
    }

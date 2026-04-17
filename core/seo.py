"""
Generadores de JSON-LD para SEO de VoltVista.

Cada función es pura: recibe datos, devuelve un dict listo para json.dumps.
Se llama desde main.py (schema global) y desde rutas que necesiten schemas extra.
"""


def _parse_areas(service_area: str) -> list[str]:
    """Divide cfg.service_area en lista limpia de ciudades.
    Recibe string separado por comas (e.g. "Orlando, Kissimmee").
    Devuelve list[str] sin espacios ni elementos vacíos."""
    return [a.strip() for a in (service_area or "").split(",") if a.strip()]


def _build_postal_address(cfg) -> dict:
    """Construye el subschema PostalAddress del negocio.
    Recibe cfg con address/city/state/zip_code.
    Devuelve dict PostalAddress anidable en LocalBusiness."""
    return {
        "@type": "PostalAddress",
        "streetAddress": cfg.address,
        "addressLocality": cfg.city,
        "addressRegion": cfg.state,
        "postalCode": cfg.zip_code,
        "addressCountry": "US",
    }


def _build_geo(cfg) -> dict:
    """Construye el subschema GeoCoordinates.
    Recibe cfg con lat y lng (float).
    Devuelve dict anidable en LocalBusiness para que Google sitúe el negocio."""
    return {
        "@type": "GeoCoordinates",
        "latitude": cfg.lat,
        "longitude": cfg.lng,
    }


def build_local_business_schema(cfg) -> dict:
    """Construye JSON-LD LocalBusiness + Electrician.
    Recibe cfg (instancia Settings con NAP, geo, horario).
    Existe para que Google muestre VoltVista en panel local y Maps."""
    return {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "Electrician"],
        "name": cfg.business_name,
        "url": cfg.business_url,
        "telephone": cfg.phone,
        "email": cfg.email,
        "logo": cfg.logo_url,
        "address": _build_postal_address(cfg),
        "geo": _build_geo(cfg),
        "openingHours": cfg.hours,
        "areaServed": _parse_areas(cfg.service_area),
        "sameAs": [],
        "priceRange": "$$",
    }


def build_aggregate_rating_schema(rating: float, count: int) -> dict:
    """Construye JSON-LD AggregateRating para la página de reseñas.
    Recibe rating (media 1-5) y count (total de reseñas).
    Devuelve dict anidable en LocalBusiness para rich snippets de estrellas."""
    return {
        "@type": "AggregateRating",
        "ratingValue": rating,
        "reviewCount": count,
        "bestRating": 5,
        "worstRating": 1,
    }


def build_service_schema(cfg, service_name: str, service_url: str, description: str) -> dict:
    """Construye JSON-LD Service para una landing de servicio concreta.
    Recibe cfg (provider) y datos del servicio (nombre, URL, descripción).
    Devuelve dict listo para json.dumps en la plantilla de la landing."""
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": service_name,
        "description": description,
        "url": service_url,
        "provider": {
            "@type": "LocalBusiness",
            "name": cfg.business_name,
            "url": cfg.business_url,
        },
        "areaServed": _parse_areas(cfg.service_area),
    }


def build_breadcrumb_schema(items: list[dict]) -> dict:
    """Construye JSON-LD BreadcrumbList a partir de una lista ordenada.
    Recibe items con {"name": str, "url": str} en orden jerárquico.
    Devuelve dict para que Google muestre breadcrumbs en SERP."""
    elements = [
        {
            "@type": "ListItem",
            "position": i + 1,
            "name": item["name"],
            "item": item["url"],
        }
        for i, item in enumerate(items)
    ]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }

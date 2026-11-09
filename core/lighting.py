"""
Servicios de iluminacion (data/lighting_services.json): una sola fuente para el
menu del nav, las tarjetas del hub, las paginas hijas, el sitemap y el schema.

Mismo patron que core/posts.py: el contenido vive en un JSON y el codigo solo lo
lee. Anadir un servicio es anadir una entrada y subir sus fotos, sin tocar HTML.

Se lee UNA vez, al importar el modulo, y falla ruidosamente si una entrada esta
incompleta: asi el error sale en el deploy y no en la cara de un cliente.
"""

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PATH = _ROOT / "data" / "lighting_services.json"
_IMG_DIR = _ROOT / "static" / "img" / "lighting"

# Textos sin los cuales una pagina hija no se puede pintar entera.
_REQUIRED = ("slug", "nav_label", "h1", "subtitle", "card_blurb", "meta_title",
             "meta_description", "hero_image", "hero_alt", "cta_text", "cta_href")

# Listas opcionales: vacias, su seccion simplemente no se renderiza.
_LISTS = ("sections", "bullets", "gallery", "faq")

# Marca de contenido pendiente. Un borrador la puede llevar; uno publicado no.
_PLACEHOLDER = "[PLACEHOLDER]"


def _fail(service: dict, reason: str) -> None:
    """Corta el arranque con un mensaje que dice que entrada y que le pasa."""
    raise ValueError(f"lighting_services.json ({service.get('slug', '?')}): {reason}")


def _check_published(service: dict) -> None:
    """Candados que solo aplican a lo que se ve en el sitio.

    Un servicio publicado no puede llevar [PLACEHOLDER] en ningun campo, ni
    apuntar a fotos que no estan en static/img/lighting/ (saldria la imagen rota).
    """
    if _PLACEHOLDER in json.dumps(service):
        _fail(service, "published: true pero aun lleva [PLACEHOLDER]")
    files = [service["hero_image"]] + [g["file"] for g in service["gallery"]]
    missing = [f for f in files if not (_IMG_DIR / f).exists()]
    if missing:
        _fail(service, f"faltan fotos en static/img/lighting/: {', '.join(missing)}")


def _validate(service: dict) -> dict:
    """Comprueba una entrada y le pone las listas que falten como vacias.

    Recibe el dict tal cual sale del JSON; devuelve el mismo dict normalizado.
    """
    missing = [c for c in _REQUIRED if not service.get(c)]
    missing += [c for c in ("order", "published") if c not in service]
    if missing:
        _fail(service, f"faltan {', '.join(missing)}")
    for key in _LISTS:
        service.setdefault(key, [])
    if service["published"]:
        _check_published(service)
    return service


def _read() -> list[dict]:
    """Lee y valida el JSON. Devuelve todos los servicios ordenados por `order`."""
    if not _PATH.exists():
        return []
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    services = [_validate(s) for s in data.get("services", [])]
    return sorted(services, key=lambda s: s["order"])


_SERVICES = _read()


def load_services() -> list[dict]:
    """Servicios publicados, en el orden del campo `order`.

    Los borradores (published: false) no salen en ningun sitio: ni nav, ni hub,
    ni sitemap, ni su propia URL.
    """
    return [s for s in _SERVICES if s["published"]]


def get_service(slug: str) -> dict | None:
    """El servicio publicado con ese slug, o None si no existe o es borrador."""
    return next((s for s in load_services() if s["slug"] == slug), None)

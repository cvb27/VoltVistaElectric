"""
Paginas por zona (data/areas.json): una pagina /areas/{slug} por cada zona
publicada, mas los enlaces desde las pildoras de zona y el footer.

Mismo patron que core/lighting.py: el contenido vive en un JSON y el codigo
solo lo lee. Anadir una zona es anadir una entrada y subir sus fotos.

Se lee UNA vez al importar y falla ruidosamente si una entrada esta incompleta,
asi el error sale en el deploy y no en la cara de un cliente.
"""

import json
import logging
from pathlib import Path

from core.config import settings
from core.lighting import load_services
from core.seo import parse_areas

_ROOT = Path(__file__).resolve().parent.parent
_PATH = _ROOT / "data" / "areas.json"
# Las fotos de los trabajos ya viven en gallery/ o lighting/: `image` lleva la
# subcarpeta ("lighting/foto.webp") para reutilizarlas sin copiar archivos.
_IMG_ROOT = _ROOT / "static" / "img"

_REQUIRED = ("slug", "name", "meta_title", "meta_description", "h1", "subtitle", "intro")
_JOB_FIELDS = ("title", "body", "image", "alt", "service_slug")
_PLACEHOLDER = "[PLACEHOLDER]"

_log = logging.getLogger(__name__)


def _fail(area: dict, reason: str) -> None:
    """Corta el arranque con un mensaje que dice que zona y que le pasa."""
    raise ValueError(f"areas.json ({area.get('slug', '?')}): {reason}")


def _check_job(area: dict, job: dict, service_slugs: set) -> None:
    """Un trabajo publicado: campos completos, foto existente y servicio vivo.

    El servicio tiene que estar publicado: si no, el enlace del trabajo daria 404.
    """
    missing = [c for c in _JOB_FIELDS if not job.get(c)]
    if missing:
        _fail(area, f"un trabajo no tiene {', '.join(missing)}")
    if ".." in job["image"] or not (_IMG_ROOT / job["image"]).is_file():
        _fail(area, f"falta la foto static/img/{job['image']}")
    if job["service_slug"] not in service_slugs:
        _fail(area, f"service_slug '{job['service_slug']}' no es un servicio publicado")


def _check_published(area: dict) -> None:
    """Candados que solo aplican a lo que se ve en el sitio."""
    if _PLACEHOLDER in json.dumps(area):
        _fail(area, "published: true pero aun lleva [PLACEHOLDER]")
    service_slugs = {s["slug"] for s in load_services()}
    for job in area["jobs"]:
        _check_job(area, job, service_slugs)
    # Aviso y no error: la pagina se sirve igual, pero ninguna pildora ni el
    # footer la enlazaran, porque esas listas salen de BUSINESS_SERVICE_AREA.
    if area["name"] not in parse_areas(settings.service_area):
        _log.warning("areas.json (%s): '%s' no esta en BUSINESS_SERVICE_AREA; "
                     "la pagina se sirve pero no la enlaza nada", area["slug"], area["name"])


def _validate(area: dict) -> dict:
    """Comprueba una entrada y pone `jobs` y `faq` vacios si faltan."""
    missing = [c for c in _REQUIRED if not area.get(c)]
    if "published" not in area:
        missing.append("published")
    if missing:
        _fail(area, f"faltan {', '.join(missing)}")
    area.setdefault("jobs", [])
    area.setdefault("faq", [])
    if area["published"]:
        _check_published(area)
    return area


def _read() -> list[dict]:
    """Lee y valida el JSON. Devuelve todas las zonas, publicadas o no."""
    if not _PATH.exists():
        return []
    areas = [_validate(a) for a in json.loads(_PATH.read_text(encoding="utf-8")).get("areas", [])]
    slugs = [a["slug"] for a in areas]
    if len(slugs) != len(set(slugs)):
        raise ValueError("areas.json: hay slugs repetidos")
    return areas


_AREAS = _read()


def load_areas() -> list[dict]:
    """Zonas publicadas, en el orden del JSON. Los borradores no salen en nada."""
    return [a for a in _AREAS if a["published"]]


def get_area(slug: str) -> dict | None:
    """La zona publicada con ese slug, o None si no existe o es borrador."""
    return next((a for a in load_areas() if a["slug"] == slug), None)


def area_links() -> dict[str, str]:
    """{nombre de zona: URL} de las publicadas. Lo usan pildoras y footer."""
    return {a["name"]: f"/areas/{a['slug']}" for a in load_areas()}

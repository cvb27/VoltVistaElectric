"""
Fotos de la galeria del home (data/home_gallery.json), en el mismo formato
{file, alt} que la galeria de las paginas hijas (data/lighting_services.json).

Se lee UNA vez al importar y falla ruidosamente si una entrada esta incompleta
o apunta a una foto que no existe: asi el error sale en el deploy y no como
una imagen rota en la home.
"""

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PATH = _ROOT / "data" / "home_gallery.json"
_IMG_DIR = _ROOT / "static" / "img" / "gallery"


def _check(photo: dict) -> dict:
    """Valida una entrada {file, alt}. Devuelve la misma entrada si esta bien."""
    if not photo.get("file") or not photo.get("alt"):
        raise ValueError(f"home_gallery.json: entrada sin file o alt: {photo}")
    if not (_IMG_DIR / photo["file"]).exists():
        raise ValueError(f"home_gallery.json: falta static/img/gallery/{photo['file']}")
    return photo


def _read() -> list[dict]:
    """Lee y valida el JSON. Devuelve las fotos en el orden en que estan escritas."""
    if not _PATH.exists():
        return []
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    return [_check(p) for p in data.get("gallery", [])]


_PHOTOS = _read()


def load_home_gallery() -> list[dict]:
    """Fotos de la galeria del home, lista de {file, alt}. Vacia = sin seccion."""
    return _PHOTOS

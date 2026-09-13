"""
Servicios y galeria de la pagina de iluminacion (data/lighting_services.json).

Mismo patron que core/offers.py y core/posts.py: los contenidos editables viven
en un JSON y el codigo solo los lee. Anadir un servicio de iluminacion o una
foto a la galeria es editar ese archivo y desplegar — sin tocar plantillas.

Falla ruidosamente si a un servicio le falta un campo obligatorio: es preferible
un error visible en el deploy a una pagina publicada con un modulo a medias.
"""

import json
from pathlib import Path

# Ruta absoluta para no depender de desde donde se arranque el proceso.
_PATH = Path(__file__).resolve().parent.parent / "data" / "lighting_services.json"

# Campos sin los cuales el modulo de servicio no se puede pintar entero.
_REQUIRED = ("slug", "title", "subtitle", "body", "bullets",
             "image", "image_alt", "cta_text", "cta_href")


def load_lighting() -> dict:
    """Devuelve {'services': [...], 'gallery': [...]}.

    La galeria es una lista de cualquier longitud: la plantilla itera sobre
    ella, asi que anadir o quitar fotos no rompe el layout.
    """
    if not _PATH.exists():
        return {"services": [], "gallery": []}

    data = json.loads(_PATH.read_text(encoding="utf-8"))

    for s in data.get("services", []):
        faltan = [c for c in _REQUIRED if not s.get(c)]
        if faltan:
            raise ValueError(
                f"Servicio de iluminacion incompleto ({s.get('slug', '?')}): "
                f"faltan {', '.join(faltan)}"
            )

    return {"services": data.get("services", []), "gallery": data.get("gallery", [])}

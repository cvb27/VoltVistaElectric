"""
Lectura del indice del blog (data/blog_posts.json).

Un solo sitio que lo abre, para que /blog y /sitemap.xml nunca se
desincronicen: publicar un post lo hace aparecer en los dos a la vez.
"""

import json
from pathlib import Path

# Ruta absoluta y no relativa: asi funciona sin depender de desde donde se
# arranque el proceso. Mismo patron que core/offers.py con surge_offers.json.
_PATH = Path(__file__).resolve().parent.parent / "data" / "blog_posts.json"


def load_posts() -> list[dict]:
    """Devuelve los posts del indice, o lista vacia si el archivo no esta.

    No revienta cuando falta el archivo a proposito: un blog sin posts es una
    pagina vacia, no un error de servidor — y ahora tambien lo lee el sitemap,
    donde un fallo dejaria a Google sin ninguna URL.
    """
    if not _PATH.exists():
        return []
    return json.loads(_PATH.read_text(encoding="utf-8"))

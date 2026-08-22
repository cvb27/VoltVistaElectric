"""
Planes y precios de la oferta de surge protector.

Fuente unica: data/surge_offers.json. Para cambiar un precio o un bullet se
edita ese archivo y se despliega — no hay que tocar codigo ni reiniciar nada.

El precio SIEMPRE se toma de aqui, del lado del servidor. Nunca de un campo
del formulario: eso permitiria que un cliente pague lo que quiera.
"""

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "data" / "surge_offers.json"


def load_offers() -> dict:
    """Devuelve {'from_price': int, 'plans': [...]}.

    Falla ruidosamente si el JSON esta mal formado o le falta un campo:
    es preferible un error visible en el deploy a una pagina con precios rotos."""

    with open(_PATH, encoding="utf-8") as f:
        data = json.load(f)

    for plan in data["plans"]:
        if not plan.get("key") or not isinstance(plan.get("price"), (int, float)):
            raise ValueError(f"Plan invalido en surge_offers.json: {plan}")

    return data


def get_plan(key: str) -> dict:
    """Busca un plan por su key. Lanza KeyError si no existe.

    Lanza en vez de devolver None a proposito: quien llama necesita el precio
    y no puede seguir sin el, asi que un None solo retrasaria el fallo hasta
    un p["price"] con un TypeError mucho mas dificil de leer. Las rutas ya
    envuelven la llamada en un try/except que espera KeyError.
    """
    plan = next((p for p in load_offers()["plans"] if p["key"] == key), None)
    if plan is None:
        raise KeyError(f"Plan desconocido: {key!r}")
    return plan
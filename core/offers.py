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


def get_plan(key: str) -> dict | None:
    """Busca un plan por su key. Devuelve None si no existe.

    Lo usara la Fase 3 para tomar el precio del servidor al crear el cobro."""

    return next((p for p in load_offers()["plans"] if p["key"] == key), None)
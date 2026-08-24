"""
Planes y precios de la oferta de surge protector.

Fuente unica: data/surge_offers.json. Para cambiar un precio o un bullet se
edita ese archivo y se despliega — no hay que tocar codigo ni reiniciar nada.

El precio SIEMPRE se toma de aqui, del lado del servidor. Nunca de un campo
del formulario: eso permitiria que un cliente pague lo que quiera.
"""

import json
from pathlib import Path

from core.booking import DEPOSIT
from core.discounts import percent_for

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


def quote(plan: dict, code: str = "") -> dict:
    """Desglose de precios de una reserva. Unica fuente del calculo.

    Existe porque "precio - deposito" estaba repetido en cuatro sitios de
    routes/booking.py, y el descuento habria que meterlo en los cuatro: el
    primero que se olvidara cobraria de mas.

    El descuento baja el TOTAL, nunca el deposito. El cliente paga hoy lo
    mismo de siempre y lo que se reduce es lo que queda al terminar el trabajo.

    Devuelve tambien `percent` y `code` porque la pagina los muestra: decir
    solo "10% off" obligaria al cliente a fiarse del redondeo.
    """
    percent = percent_for(code)

    # Redondeo al dolar mas cercano con los medios hacia arriba. No se usa
    # round() porque en Python hace redondeo bancario — round(150.5) da 150 —
    # y en dinero eso sorprende a cualquiera que revise la cuenta.
    discount = int(plan["price"] * percent / 100 + 0.5) if percent else 0

    return {
        "plan": plan,
        "code": code.strip().upper() if percent else "",
        "percent": percent,
        "discount": discount,
        "total": plan["price"] - discount,
        "deposit": DEPOSIT,
        "balance": plan["price"] - discount - DEPOSIT,
    }

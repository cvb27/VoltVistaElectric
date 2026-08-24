"""
Codigos de descuento (data/discounts.json).

Se crea uno cada varios meses, asi que la lista vive en un JSON que se edita y
se despliega — igual que los precios de surge_offers.json. Sin panel ni tabla
en la base: seria mucha maquinaria para media docena de codigos al ano.
"""

import json
from datetime import date
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "data" / "discounts.json"


def _load() -> list[dict]:
    """Lee y valida la lista. Falla ruidosamente si algo esta mal escrito.

    Un "percent": 100 tecleado en vez de 10 regalaria el trabajo entero. Un
    error visible al primer request es mucho mejor que un precio absurdo
    cobrado en silencio. Lo mismo con una fecha mal formada.
    """
    if not _PATH.exists():
        return []

    codes = json.loads(_PATH.read_text(encoding="utf-8"))
    for d in codes:
        if not 1 <= int(d["percent"]) <= 90:
            raise ValueError(f"Descuento fuera de rango en discounts.json: {d}")
        date.fromisoformat(d["expires"])      # revienta si la fecha esta mal
    return codes


def percent_for(code: str, today: date | None = None) -> int:
    """Porcentaje de descuento de un codigo. 0 si no existe o ya caduco.

    Devolver 0 en vez de lanzar simplifica a quien llama: un codigo invalido y
    "sin codigo" se tratan igual — no hay descuento y punto.

    La comparacion ignora mayusculas porque la gente teclea estos codigos
    desde una foto o un papel. `today` solo se pasa en las pruebas.
    """
    if not code:
        return 0

    today = today or date.today()
    wanted = code.strip().upper()

    for d in _load():
        if d["code"].upper() == wanted and date.fromisoformat(d["expires"]) >= today:
            return int(d["percent"])
    return 0

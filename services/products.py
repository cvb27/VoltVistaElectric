import json
from pathlib import Path
from typing import List, Dict

DATA_PATH = Path("data/products.json")


def load_products() -> List[Dict]:
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

import json
from pathlib import Path
from typing import List, Dict

DATA_PATH = Path("data/reviews.json")


def load_reviews() -> List[Dict]:
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

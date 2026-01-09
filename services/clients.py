import json
from pathlib import Path
from typing import List, Dict

DATA_PATH = Path("data/clients.json")


def load_clients() -> List[Dict]:
    """
    Cada item:
    {
      "name": "LakeView Hotel",
      "type": "hotel" | "hoa" | "commercial",
      "logo": "/static/img/clients/sample-hotel.png",
      "highlight": true,
      "note": "Maintenance partner"
    }
    """
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def split_highlights(clients: List[Dict]):
    highlights = [c for c in clients if c.get("highlight")]
    others = [c for c in clients if not c.get("highlight")]
    return highlights, others

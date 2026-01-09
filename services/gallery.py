import json
from pathlib import Path
from typing import List, Dict

DATA_PATH = Path("data/gallery.json")


def load_gallery() -> List[Dict]:
    """
    Cada item:
    {
      "title": "...",
      "before": "/static/img/gallery/job1.jpg",
      "after": "/static/img/gallery/job1_after.jpg",
      "tag": "Panel Upgrade"
    }
    """
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

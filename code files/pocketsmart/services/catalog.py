from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def load_catalog(name: str) -> list[dict[str, Any]]:
    path = DATA / f"{name}_catalog.json"
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return list(payload["items"])


def label(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out["sample_data"] = True
    out["label"] = "sample data"
    return out

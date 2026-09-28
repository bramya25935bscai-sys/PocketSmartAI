"""Central configuration. Model IDs live here so they can change without code edits."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PLACEHOLDER_KEYS = {"", "your-key-here", "changeme", "placeholder", "none", "xxx"}


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


GEMINI_API_KEY = _env("GEMINI_API_KEY")
GEMINI_MODEL = _env("GEMINI_MODEL") or _env("GEMINI_FLASH_MODEL") or "gemini-2.0-flash"
FLASK_SECRET_KEY = _env("FLASK_SECRET_KEY") or "pocketsmart-dev-secret"
FLASK_PORT = int(_env("FLASK_PORT") or "5000")
MAX_UPLOAD_MB = int(_env("MAX_UPLOAD_MB") or "4")
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

DEMO_MODE = GEMINI_API_KEY.lower() in PLACEHOLDER_KEYS


def health_payload() -> dict:
    return {
        "status": "ok",
        "project": "PocketSmart AI",
        "mode": "demo" if DEMO_MODE else "live",
        "model": GEMINI_MODEL,
        "demo_mode": DEMO_MODE,
    }

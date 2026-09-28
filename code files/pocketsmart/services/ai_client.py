"""Gemini client with demo mode and graceful fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pocketsmart.config import DEMO_MODE, GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = (
    "Live AI is unavailable (rate limit, invalid key, timeout, or demo mode). "
    "Showing curated sample-data recommendations instead."
)


def parse_json_payload(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
        return None


def generate_structured(prompt: str, image_bytes: bytes | None = None) -> tuple[dict | None, str]:
    """Return (parsed_json_or_None, source) where source is live|demo|fallback."""
    if DEMO_MODE:
        return None, "demo"

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        parts: list[Any] = [prompt]
        if image_bytes:
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=parts,
            config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=2048),
        )
        text = getattr(response, "text", None) or ""
        parsed = parse_json_payload(text)
        if parsed:
            return parsed, "live"
        logger.warning("Gemini returned non-JSON; using fallback.")
        return None, "fallback"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini call failed: %s", exc)
        return None, "fallback"

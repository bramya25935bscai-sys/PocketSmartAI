"""Input/output helpers and validation (no hard-coded secrets)."""

from __future__ import annotations

from typing import Any

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MIN_BUDGET = 500


class ValidationError(ValueError):
    def __init__(self, message: str, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.code = code


def as_int(value: Any, field: str, minimum: int | None = None) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a whole number.") from None
    if minimum is not None and n < minimum:
        raise ValidationError(f"{field} must be at least {minimum}.")
    return n


def as_str(value: Any, field: str, allowed: list[str] | None = None) -> str:
    s = str(value or "").strip()
    if not s:
        raise ValidationError(f"{field} is required.")
    if allowed and s.lower() not in [a.lower() for a in allowed]:
        raise ValidationError(f"{field} must be one of: {', '.join(allowed)}.")
    return s


def validate_budget(value: Any) -> int:
    n = as_int(value, "budget", minimum=1)
    if n <= 0:
        raise ValidationError("budget must be greater than zero.", "budget_invalid")
    return n


def too_small_budget(budget: int, floor: int) -> None:
    if budget < floor:
        raise ValidationError(
            f"Budget ₹{budget} is too small for this request. Please use at least ₹{floor}.",
            "budget_too_small",
        )

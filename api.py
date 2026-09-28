from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from pocketsmart.config import MAX_UPLOAD_BYTES, health_payload
from pocketsmart.models.schemas import (
    ALLOWED_IMAGE_TYPES,
    ValidationError,
    as_int,
    as_str,
    too_small_budget,
    validate_budget,
)
from pocketsmart.services.recommend import recommend_home, recommend_jewelry, recommend_party

api_bp = Blueprint("api", __name__)


def _push_history(result: dict) -> None:
    hist = session.get("history", [])
    hist.insert(
        0,
        {
            "planner": result.get("planner"),
            "budget": result.get("budget"),
            "total": result.get("total"),
            "summary": result.get("summary"),
            "item_count": len(result.get("items") or []),
        },
    )
    session["history"] = hist[:20]
    session.modified = True


@api_bp.get("/health")
def health():
    return jsonify(health_payload())


@api_bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or request.form
    name = as_str(data.get("name"), "name")
    email = as_str(data.get("email"), "email")
    session["user"] = {"name": name, "email": email}
    return jsonify({"ok": True, "user": session["user"]})


@api_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or request.form
    email = as_str(data.get("email"), "email")
    session["user"] = {"name": email.split("@")[0], "email": email}
    return jsonify({"ok": True, "user": session["user"]})


@api_bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@api_bp.get("/api/history")
def history_api():
    return jsonify({"history": session.get("history", []), "user": session.get("user")})


@api_bp.post("/generate-home")
def generate_home():
    try:
        data = request.get_json(silent=True) or {}
        budget = validate_budget(data.get("budget"))
        rooms = data.get("rooms") or []
        if isinstance(rooms, str):
            rooms = [r.strip() for r in rooms.split(",") if r.strip()]
        if not rooms:
            raise ValidationError("Select at least one room.")
        qty = data.get("quantities") or {}
        qty = {
            "lights": as_int(qty.get("lights", 0), "lights", 0),
            "fans": as_int(qty.get("fans", 0), "fans", 0),
            "dining_tables": as_int(qty.get("dining_tables", 0), "dining_tables", 0),
            "sofa": as_int(qty.get("sofa", 0), "sofa", 0),
            "bed": as_int(qty.get("bed", 0), "bed", 0),
            "storage": as_int(qty.get("storage", 0), "storage", 0),
        }
        if sum(qty.values()) == 0:
            raise ValidationError("Enter at least one quantity.")
        too_small_budget(budget, 2000)
        result = recommend_home(budget, rooms, qty)
        _push_history(result)
        return jsonify(result)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400


@api_bp.post("/generate-party")
def generate_party():
    try:
        data = request.get_json(silent=True) or {}
        budget = validate_budget(data.get("budget"))
        guests = as_int(data.get("guests"), "guests", 1)
        event = as_str(
            data.get("event_type") or data.get("event"),
            "event_type",
            ["birthday", "wedding", "corporate", "anniversary", "casual"],
        )
        venue = as_str(data.get("venue") or "home", "venue")
        too_small_budget(budget, 3000)
        result = recommend_party(budget, guests, event, venue)
        _push_history(result)
        return jsonify(result)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400


@api_bp.post("/generate-jewelry")
def generate_jewelry():
    try:
        if request.content_type and "multipart" in request.content_type:
            budget = validate_budget(request.form.get("budget"))
            occasion = as_str(request.form.get("occasion"), "occasion")
            style = as_str(request.form.get("style") or "classic", "style")
            file = request.files.get("outfit")
            image_bytes = None
            if file and file.filename:
                fname = file.filename.lower()
                mime = (file.mimetype or "").lower()
                ok_ext = fname.endswith((".png", ".jpg", ".jpeg", ".webp"))
                if mime not in ALLOWED_IMAGE_TYPES and not ok_ext:
                    raise ValidationError("Please upload a PNG, JPEG or WebP image.", "invalid_image")
                if not ok_ext:
                    raise ValidationError("Please upload a PNG, JPEG or WebP image.", "invalid_image")
                raw = file.read()
                if len(raw) > MAX_UPLOAD_BYTES:
                    raise ValidationError("Image is too large.", "file_too_large")
                if len(raw) < 32:
                    raise ValidationError("Image file is empty or invalid.", "invalid_image")
                image_bytes = raw
        else:
            data = request.get_json(silent=True) or {}
            budget = validate_budget(data.get("budget"))
            occasion = as_str(data.get("occasion"), "occasion")
            style = as_str(data.get("style") or "classic", "style")
            image_bytes = None
        too_small_budget(budget, 800)
        result = recommend_jewelry(budget, occasion, style, image_bytes=image_bytes)
        _push_history(result)
        return jsonify(result)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), 400


@api_bp.errorhandler(ValidationError)
def _ve(exc: ValidationError):
    return jsonify({"error": str(exc), "code": exc.code}), 400

from flask import Blueprint, render_template, session

from pocketsmart.config import DEMO_MODE, GEMINI_MODEL

pages_bp = Blueprint("pages", __name__)


def _ctx(**extra):
    data = {
        "demo_mode": DEMO_MODE,
        "model": GEMINI_MODEL,
        "user": session.get("user"),
        "history": session.get("history", []),
    }
    data.update(extra)
    return data


@pages_bp.get("/")
def home():
    return render_template("index.html", **_ctx())


@pages_bp.get("/login")
def login_page():
    return render_template("login.html", **_ctx())


@pages_bp.get("/register")
def register_page():
    return render_template("register.html", **_ctx())


@pages_bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html", **_ctx())


@pages_bp.get("/home-planner")
def home_planner():
    return render_template("home_planner.html", **_ctx())


@pages_bp.get("/party-planner")
def party_planner():
    return render_template("party_planner.html", **_ctx())


@pages_bp.get("/jewelry-planner")
def jewelry_planner():
    return render_template("jewelry_planner.html", **_ctx())


@pages_bp.get("/history")
def history():
    return render_template("history.html", **_ctx())


@pages_bp.get("/testimonials")
def testimonials():
    return render_template("testimonials.html", **_ctx())

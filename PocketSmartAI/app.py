from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from google import genai
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3
import os
import time
import uuid

# --------------------------------------------------
# BASIC SETUP
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "pocketsmart-secret-key-change-later")

DATABASE = "pocketsmart.db"
UPLOAD_FOLDER = os.path.join("static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            planner TEXT NOT NULL,
            budget TEXT,
            requirements TEXT,
            recommendation TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# --------------------------------------------------
# LOGIN REQUIRED
# --------------------------------------------------

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# BASIC PAGES
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="Email and password are required."
            )

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        if len(password) < 6:
            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO users
                (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    hashed_password,
                    datetime.now().isoformat()
                )
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

    return render_template("register.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name")
    )


# --------------------------------------------------
# PLANNER PAGES
# --------------------------------------------------

@app.route("/party")
def party():
    return render_template("party.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/jewellery")
def jewellery():
    return render_template("jewellery.html")


@app.route("/ai-planner")
def ai_planner():
    return render_template("ai_planner.html")


# --------------------------------------------------
# AI PROMPT
# --------------------------------------------------

def create_prompt(planner, budget, details):

    return f"""
You are PocketSmart AI, a practical personal planning assistant.

Planner:
{planner}

User Budget:
{budget}

User Requirements:
{details}

Create a practical and realistic plan.

Your response must include:

1. Budget breakdown
2. Important things to consider
3. Money-saving ideas
4. Recommended priorities
5. Simple step-by-step plan
6. Estimated spending categories

Use Indian Rupees (₹) when discussing money.

Keep the answer clear, useful and easy to understand.

Do not make unrealistic promises.
"""


# --------------------------------------------------
# LOCAL FALLBACK
# --------------------------------------------------

def fallback_recommendation(planner, budget, details):

    return f"""
PocketSmart AI Quick Plan

Planner: {planner}
Budget: ₹{budget}

Based on your requirements:

{details}

Suggested approach:

1. Set aside the most important expenses first.
2. Keep around 10% of the total budget as an emergency buffer.
3. Compare at least 2-3 vendors before spending.
4. Avoid unnecessary premium add-ons.
5. Track every expense in a simple list.

Suggested budget structure:

• Main requirements: 60%
• Secondary requirements: 20%
• Decoration / extras: 10%
• Emergency buffer: 10%

This is a basic backup plan. Gemini AI is temporarily unavailable,
so you can retry later for a more detailed recommendation.
"""


# --------------------------------------------------
# GEMINI AI
# --------------------------------------------------

def generate_ai_response(prompt):

    if client is None:
        return None, "Gemini API key not configured."

    models = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite"
    ]

    last_error = ""

    for model in models:

        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response and response.text:
                    return response.text, None

                last_error = "Empty response from Gemini."

            except Exception as e:

                last_error = str(e)

                error_text = str(e).lower()

                temporary_error = (
                    "503" in error_text
                    or "unavailable" in error_text
                    or "high demand" in error_text
                    or "429" in error_text
                    or "resource exhausted" in error_text
                )

                if temporary_error:
                    time.sleep(2 ** attempt)
                    continue

                # For model/key errors, move to fallback model
                break

    return None, last_error


# --------------------------------------------------
# AI RECOMMENDATION API
# --------------------------------------------------

@app.route("/ai-recommendation", methods=["POST"])
def ai_recommendation():

    data = request.get_json(silent=True) or {}

    planner = data.get("planner", "").strip()
    budget = data.get("budget", "").strip()
    details = data.get("details", "").strip()

    if not planner:
        return jsonify({
            "success": False,
            "message": "Please select a planner."
        })

    if not details:
        return jsonify({
            "success": False,
            "message": "Please enter your requirements."
        })

    prompt = create_prompt(
        planner,
        budget,
        details
    )

    recommendation, error = generate_ai_response(prompt)

    # --------------------------------------------------
    # GEMINI FAILED -> LOCAL BACKUP
    # --------------------------------------------------

    if not recommendation:

        recommendation = fallback_recommendation(
            planner,
            budget,
            details
        )

        source = "backup"

    else:

        source = "gemini"


    # --------------------------------------------------
    # SAVE HISTORY IF USER LOGGED IN
    # --------------------------------------------------

    if "user_id" in session:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO plans
            (
                user_id,
                planner,
                budget,
                requirements,
                recommendation,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                planner,
                budget,
                details,
                recommendation,
                datetime.now().isoformat()
            )
        )

        conn.commit()
        conn.close()


    return jsonify({
        "success": True,
        "recommendation": recommendation,
        "source": source
    })


# --------------------------------------------------
# HISTORY
# --------------------------------------------------

@app.route("/history")
@login_required
def history():

    conn = get_db()

    plans = conn.execute(
        """
        SELECT *
        FROM plans
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "history.html",
        plans=plans
    )


@app.route("/api/history")
@login_required
def api_history():

    conn = get_db()

    plans = conn.execute(
        """
        SELECT
            id,
            planner,
            budget,
            requirements,
            recommendation,
            created_at
        FROM plans
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return jsonify({
        "success": True,
        "history": [dict(plan) for plan in plans]
    })


# --------------------------------------------------
# DELETE HISTORY ITEM
# --------------------------------------------------

@app.route("/delete-plan/<int:plan_id>", methods=["POST"])
@login_required
def delete_plan(plan_id):

    conn = get_db()

    conn.execute(
        """
        DELETE FROM plans
        WHERE id = ? AND user_id = ?
        """,
        (
            plan_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("history"))


# --------------------------------------------------
# JEWELLERY IMAGE UPLOAD
# --------------------------------------------------

@app.route("/upload-jewellery", methods=["POST"])
def upload_jewellery():

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "No image selected."
        })

    image = request.files["image"]

    if image.filename == "":
        return jsonify({
            "success": False,
            "message": "Please select an image."
        })

    allowed_extensions = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }

    extension = image.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        return jsonify({
            "success": False,
            "message": "Only JPG, JPEG, PNG and WEBP images are allowed."
        })

    filename = f"{uuid.uuid4().hex}.{extension}"

    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    image.save(path)

    return jsonify({
        "success": True,
        "image_url": f"/static/uploads/{filename}"
    })


# --------------------------------------------------
# SAVE NORMAL PLAN
# --------------------------------------------------

@app.route("/save-plan", methods=["POST"])
@login_required
def save_plan():

    data = request.get_json(silent=True) or {}

    planner = data.get("planner", "").strip()
    budget = data.get("budget", "").strip()
    requirements = data.get("requirements", "").strip()
    recommendation = data.get("recommendation", "").strip()

    if not planner:
        return jsonify({
            "success": False,
            "message": "Planner is required."
        })

    conn = get_db()

    conn.execute(
        """
        INSERT INTO plans
        (
            user_id,
            planner,
            budget,
            requirements,
            recommendation,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            planner,
            budget,
            requirements,
            recommendation,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Plan saved successfully."
    })


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "PocketSmart AI is running",
        "gemini": bool(client),
        "database": os.path.exists(DATABASE)
    })


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
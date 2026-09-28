"""API, validation, budget, session, image and fallback tests."""

from unittest.mock import patch

from pocketsmart.services.recommend import enforce_budget, fallback_home, fallback_party, fallback_jewelry


def test_health_demo_mode(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["mode"] in {"demo", "live"}
    assert "demo_mode" in data


def test_home_page(client):
    assert b"PocketSmart AI" in client.get("/").data
    assert b"Demo mode" in client.get("/").data


def test_home_valid_budget(client):
    res = client.post(
        "/generate-home",
        json={
            "budget": 80000,
            "rooms": ["living", "kitchen", "bedroom"],
            "quantities": {"lights": 4, "fans": 3, "dining_tables": 1, "sofa": 1, "bed": 1, "storage": 1},
        },
    )
    data = res.get_json()
    assert res.status_code == 200
    assert data["total"] <= data["budget"]
    assert data["items"]
    assert all(i.get("sample_data") for i in data["items"])


def test_party_valid(client):
    res = client.post(
        "/generate-party",
        json={"budget": 50000, "guests": 40, "event_type": "birthday", "venue": "home"},
    )
    data = res.get_json()
    assert res.status_code == 200
    assert data["total"] <= 50000
    assert data["guests"] == 40


def test_jewelry_valid(client):
    res = client.post("/generate-jewelry", json={"budget": 15000, "occasion": "wedding guest", "style": "classic"})
    data = res.get_json()
    assert res.status_code == 200
    assert data["total"] <= 15000


def test_zero_budget_rejected(client):
    res = client.post("/generate-home", json={"budget": 0, "rooms": ["living"], "quantities": {"lights": 1}})
    assert res.status_code == 400


def test_negative_budget_rejected(client):
    res = client.post("/generate-party", json={"budget": -10, "guests": 5, "event_type": "birthday", "venue": "home"})
    assert res.status_code == 400


def test_budget_too_small(client):
    res = client.post(
        "/generate-home",
        json={"budget": 100, "rooms": ["living"], "quantities": {"lights": 1}},
    )
    assert res.status_code == 400
    assert res.get_json()["code"] == "budget_too_small"


def test_missing_rooms(client):
    res = client.post("/generate-home", json={"budget": 80000, "rooms": [], "quantities": {"lights": 1}})
    assert res.status_code == 400


def test_invalid_event_type(client):
    res = client.post("/generate-party", json={"budget": 50000, "guests": 10, "event_type": "alien", "venue": "home"})
    assert res.status_code == 400


def test_zero_guests(client):
    res = client.post("/generate-party", json={"budget": 50000, "guests": 0, "event_type": "birthday", "venue": "home"})
    assert res.status_code == 400


def test_invalid_image(client):
    from io import BytesIO

    res = client.post(
        "/generate-jewelry",
        data={
            "budget": "15000",
            "occasion": "party",
            "style": "modern",
            "outfit": (BytesIO(b"not-an-image"), "notes.txt"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 400


def test_valid_image_upload(client, png_bytes):
    from io import BytesIO

    res = client.post(
        "/generate-jewelry",
        data={
            "budget": "15000",
            "occasion": "wedding guest",
            "style": "traditional",
            "outfit": (BytesIO(png_bytes), "outfit.png"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] <= 15000
    assert data.get("outfit_analysis")


def test_session_history(client):
    client.post(
        "/generate-party",
        json={"budget": 50000, "guests": 20, "event_type": "corporate", "venue": "hotel"},
    )
    hist = client.get("/api/history").get_json()
    assert hist["history"]
    assert hist["history"][0]["planner"] == "party"


def test_login_session(client):
    res = client.post("/auth/login", json={"email": "a@b.com", "password": "x"})
    assert res.status_code == 200
    assert res.get_json()["user"]["email"] == "a@b.com"


def test_ai_failure_fallback(client):
    with patch("pocketsmart.services.recommend.generate_structured", return_value=(None, "fallback")):
        res = client.post(
            "/generate-home",
            json={"budget": 80000, "rooms": ["living"], "quantities": {"lights": 2, "fans": 1}},
        )
    data = res.get_json()
    assert res.status_code == 200
    assert data["fallback"] is True
    assert data["items"]
    assert data["total"] <= 80000
    assert data["message"]


def test_invalid_ai_json_fallback(client):
    with patch(
        "pocketsmart.services.recommend.generate_structured",
        return_value=({"items": [{"id": "nope"}]}, "live"),
    ):
        res = client.post(
            "/generate-jewelry",
            json={"budget": 15000, "occasion": "party", "style": "modern"},
        )
    assert res.status_code == 200
    assert res.get_json()["items"]


def test_enforce_budget_never_exceeds():
    items = [
        {"name": "a", "price": 900, "qty": 1},
        {"name": "b", "price": 200, "qty": 1},
        {"name": "c", "price": 50, "qty": 1},
    ]
    kept = enforce_budget(items, 250)
    assert sum(i["qty"] * i["price"] for i in kept) <= 250


def test_fallback_home_respects_budget():
    items = fallback_home(80000, ["living", "kitchen"], {"lights": 4, "fans": 2, "dining_tables": 1})
    assert items
    assert sum(i["qty"] * i["price"] for i in items) <= 80000


def test_fallback_party_split():
    items = fallback_party(50000, 40, "birthday", "hotel")
    cats = {i["category"] for i in items}
    assert "catering" in cats
    assert sum(i["qty"] * i["price"] for i in items) <= 50000


def test_register_requires_name(client):
    res = client.post("/auth/register", json={"email": "x@y.com"})
    assert res.status_code == 400


def test_planner_pages_load(client):
    for path in ["/home-planner", "/party-planner", "/jewelry-planner", "/login", "/register", "/testimonials"]:
        assert client.get(path).status_code == 200

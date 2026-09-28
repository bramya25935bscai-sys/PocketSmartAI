"""Budget-capped recommendation engine with AI assist and fallback."""

from __future__ import annotations

from typing import Any

from pocketsmart.services.ai_client import FALLBACK_MESSAGE, generate_structured
from pocketsmart.services.catalog import label, load_catalog

HOME_PROMPTS = """You are PocketSmart AI. Recommend home products from this catalog JSON.
Budget INR {budget}. Rooms: {rooms}. Quantities: {qty}.
Catalog: {catalog}
Return JSON only: {{"items":[{{"id":"...","qty":1,"reason":"..."}}], "summary":"..."}}
Never exceed budget. Use only catalog ids."""

PARTY_PROMPT = """You are PocketSmart AI party planner.
Budget INR {budget}. Guests: {guests}. Event: {event}. Venue: {venue}.
Split across catering, decoration, entertainment, stay if needed.
Catalog: {catalog}
Return JSON only: {{"items":[{{"id":"...","qty":1,"reason":"..."}}], "split":{{"catering":0,"decoration":0,"entertainment":0,"stay":0}}, "summary":"..."}}
Never exceed budget."""

JEWEL_PROMPT = """You are PocketSmart AI jewelry stylist.
Budget INR {budget}. Occasion: {occasion}. Style: {style}. Outfit notes: {outfit}.
Catalog: {catalog}
Return JSON only: {{"items":[{{"id":"...","qty":1,"reason":"..."}}], "summary":"...","outfit_analysis":"..."}}
Never exceed budget."""


def _index(items: list[dict]) -> dict[str, dict]:
    return {i["id"]: i for i in items}


def enforce_budget(selected: list[dict], budget: int) -> list[dict]:
    """Greedy keep cheapest-first until under budget; qty * price."""
    priced = []
    for row in selected:
        qty = max(1, int(row.get("qty") or 1))
        price = int(row["price"])
        priced.append({**row, "qty": qty, "line_total": qty * price})
    priced.sort(key=lambda x: x["line_total"])
    kept: list[dict] = []
    total = 0
    for row in priced:
        if total + row["line_total"] <= budget:
            kept.append(row)
            total += row["line_total"]
    return kept


def fallback_home(budget: int, rooms: list[str], qty: dict[str, int]) -> list[dict]:
    catalog = load_catalog("home")
    wanted_rooms = {r.lower() for r in rooms} or {"living", "kitchen", "bedroom"}
    picks: list[dict] = []
    remaining = budget
    for cat, n in qty.items():
        n = max(0, int(n or 0))
        matches = [
            i
            for i in catalog
            if i["category"] == cat and (i["room"] in wanted_rooms or not wanted_rooms)
        ]
        matches.sort(key=lambda x: x["price"])
        for i in range(n):
            if not matches:
                break
            item = matches[i % len(matches)]
            if item["price"] <= remaining:
                picks.append({**label(item), "qty": 1, "reason": "Curated fallback for requested quantity."})
                remaining -= item["price"]
    if not picks:
        for item in sorted(catalog, key=lambda x: x["price"]):
            if item["price"] <= remaining:
                picks.append({**label(item), "qty": 1, "reason": "Budget-safe sample pick."})
                remaining -= item["price"]
            if remaining < 500:
                break
    return enforce_budget(picks, budget)


def fallback_party(budget: int, guests: int, event: str, venue: str) -> list[dict]:
    catalog = load_catalog("party")
    packs = max(1, (guests + 9) // 10)
    remaining = budget
    picks: list[dict] = []
    order = ["catering", "decoration", "entertainment"]
    if venue.lower() in {"hotel", "resort", "outstation", "oyo"}:
        order.append("stay")
    by_cat: dict[str, list] = {}
    for it in catalog:
        by_cat.setdefault(it["category"], []).append(it)
    for cat in order:
        items = sorted(by_cat.get(cat, []), key=lambda x: x["price"])
        if not items:
            continue
        qty = packs if cat == "catering" else 1
        item = items[0]
        line = item["price"] * qty
        if line <= remaining:
            picks.append(
                {
                    **label(item),
                    "qty": qty,
                    "reason": f"Fallback {cat} for {event} ({guests} guests).",
                }
            )
            remaining -= line
        elif item["price"] <= remaining:
            picks.append({**label(item), "qty": 1, "reason": f"Scaled-down {cat}."})
            remaining -= item["price"]
    return enforce_budget(picks, budget)


def fallback_jewelry(budget: int, occasion: str, style: str, colors: list[str] | None = None) -> list[dict]:
    catalog = load_catalog("jewelry")
    colors = [c.lower() for c in (colors or [])]
    scored = []
    for it in catalog:
        score = 0
        if style and style.lower() in it.get("style", "").lower():
            score += 3
        if occasion.lower() in {"wedding", "wedding guest", "bridal"} and it["style"] in {
            "bridal",
            "traditional",
            "ethnic",
        }:
            score += 2
        if colors and any(c in [x.lower() for x in it.get("colors", [])] for c in colors):
            score += 2
        scored.append((score, it))
    scored.sort(key=lambda x: (-x[0], x[1]["price"]))
    remaining = budget
    picks: list[dict] = []
    for score, it in scored:
        if it["price"] <= remaining:
            picks.append(
                {
                    **label(it),
                    "qty": 1,
                    "reason": f"Matches {occasion}/{style} (score {score}).",
                }
            )
            remaining -= it["price"]
        if len(picks) >= 5:
            break
    return enforce_budget(picks, budget)


def _hydrate(ai_items: list[dict], catalog: list[dict]) -> list[dict]:
    idx = _index(catalog)
    out = []
    for row in ai_items or []:
        base = idx.get(str(row.get("id")))
        if not base:
            continue
        out.append(
            {
                **label(base),
                "qty": int(row.get("qty") or 1),
                "reason": row.get("reason") or "AI suggestion",
            }
        )
    return out


def recommend_home(budget: int, rooms: list[str], qty: dict[str, int]) -> dict[str, Any]:
    catalog = load_catalog("home")
    parsed, source = generate_structured(
        HOME_PROMPTS.format(budget=budget, rooms=rooms, qty=qty, catalog=catalog)
    )
    items = _hydrate((parsed or {}).get("items", []), catalog) if parsed else []
    if len(items) < 2:
        items = fallback_home(budget, rooms, qty)
        source = "demo" if source == "demo" else "fallback"
        message = FALLBACK_MESSAGE
        summary = "Curated home plan from sample catalogs (IKEA, Amazon, Flipkart)."
    else:
        items = enforce_budget(items, budget)
        message = None
        summary = (parsed or {}).get("summary") or "AI home plan within budget."
    total = sum(i["qty"] * i["price"] for i in items)
    return {
        "planner": "home",
        "budget": budget,
        "total": total,
        "remaining": budget - total,
        "items": items,
        "source": source,
        "fallback": source != "live",
        "message": message,
        "summary": summary,
        "sample_data": True,
        "rooms": rooms,
        "quantities": qty,
    }


def recommend_party(budget: int, guests: int, event: str, venue: str) -> dict[str, Any]:
    catalog = load_catalog("party")
    parsed, source = generate_structured(
        PARTY_PROMPT.format(budget=budget, guests=guests, event=event, venue=venue, catalog=catalog)
    )
    items = _hydrate((parsed or {}).get("items", []), catalog) if parsed else []
    if len(items) < 2:
        items = fallback_party(budget, guests, event, venue)
        source = "demo" if source == "demo" else "fallback"
        message = FALLBACK_MESSAGE
        summary = f"Sample {event} plan for {guests} guests."
        split = {}
    else:
        items = enforce_budget(items, budget)
        message = None
        summary = (parsed or {}).get("summary") or "AI party plan."
        split = (parsed or {}).get("split") or {}
    if not split:
        split = {}
        for it in items:
            split[it["category"]] = split.get(it["category"], 0) + it["qty"] * it["price"]
    total = sum(i["qty"] * i["price"] for i in items)
    return {
        "planner": "party",
        "budget": budget,
        "total": total,
        "remaining": budget - total,
        "items": items,
        "split": split,
        "source": source,
        "fallback": source != "live",
        "message": message,
        "summary": summary,
        "sample_data": True,
        "guests": guests,
        "event": event,
        "venue": venue,
    }


def recommend_jewelry(
    budget: int,
    occasion: str,
    style: str,
    outfit_notes: str = "",
    colors: list[str] | None = None,
    image_bytes: bytes | None = None,
) -> dict[str, Any]:
    catalog = load_catalog("jewelry")
    prompt = JEWEL_PROMPT.format(
        budget=budget, occasion=occasion, style=style, outfit=outfit_notes or "none", catalog=catalog
    )
    parsed, source = generate_structured(prompt, image_bytes=image_bytes)
    items = _hydrate((parsed or {}).get("items", []), catalog) if parsed else []
    analysis = (parsed or {}).get("outfit_analysis") if parsed else None
    if image_bytes and not analysis:
        analysis = (
            "Outfit image processed locally in demo mode: warm gold and jewel tones suggested "
            "for a wedding-guest look."
            if source == "demo"
            else "Could not analyse the outfit image; matching by occasion and style."
        )
    if len(items) < 2:
        items = fallback_jewelry(budget, occasion, style, colors)
        source = "demo" if source == "demo" else "fallback"
        message = FALLBACK_MESSAGE
        summary = f"Sample jewelry picks for {occasion} ({style})."
    else:
        items = enforce_budget(items, budget)
        message = None
        summary = (parsed or {}).get("summary") or "AI jewelry plan."
    total = sum(i["qty"] * i["price"] for i in items)
    return {
        "planner": "jewelry",
        "budget": budget,
        "total": total,
        "remaining": budget - total,
        "items": items,
        "source": source,
        "fallback": source != "live",
        "message": message,
        "summary": summary,
        "outfit_analysis": analysis,
        "sample_data": True,
        "occasion": occasion,
        "style": style,
    }

"""Walk every UI scenario and save numbered PNGs."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE_ROOT = Path(__file__).resolve().parent.parent   # "code files" folder
ROOT = CODE_ROOT.parent                              # repository root
SHOT = ROOT / "docs" / "screenshots"
SHOT.mkdir(parents=True, exist_ok=True)
OUTFIT = CODE_ROOT / "pocketsmart" / "static" / "img" / "sample_outfit.png"
BASE = "http://127.0.0.1:5000"

captions = []


def shot(page, name, caption, mobile=False):
    path = SHOT / name
    page.screenshot(path=str(path), full_page=False)
    captions.append({"file": name, "caption": caption, "mobile": mobile})
    print("saved", name)


def main():
    proc = subprocess.Popen(
        [sys.executable, "-m", "pocketsmart.app"],
        cwd=str(CODE_ROOT),
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "GEMINI_API_KEY": "", "PYTHONPATH": str(CODE_ROOT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    time.sleep(1.5)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1366, "height": 768})
            page.goto(BASE, wait_until="networkidle")
            shot(page, "01_home.png", "Landing page with Demo mode badge and three planners.")
            page.goto(BASE + "/register", wait_until="networkidle")
            shot(page, "02_register.png", "Registration form with sample user.")
            page.click("button[type=submit]")
            page.wait_for_url("**/dashboard")
            shot(page, "03_dashboard.png", "Dashboard after register.")
            page.goto(BASE + "/login", wait_until="networkidle")
            shot(page, "04_login.png", "Login page.")
            page.goto(BASE + "/home-planner", wait_until="networkidle")
            shot(page, "05_home_planner_form.png", "Home planner: Rs 80,000, living+kitchen+bedroom.")
            page.click("button[type=submit]")
            page.wait_for_selector("#budget-totals")
            shot(page, "06_home_results.png", "Home recommendations within Rs 80,000 (sample data).")
            page.goto(BASE + "/party-planner", wait_until="networkidle")
            shot(page, "07_party_form.png", "Party planner: birthday, 40 guests, Rs 50,000.")
            page.click("button[type=submit]")
            page.wait_for_selector("#budget-totals")
            shot(page, "08_party_results.png", "Party split across catering, décor, entertainment.")
            page.goto(BASE + "/jewelry-planner", wait_until="networkidle")
            shot(page, "09_jewelry_form.png", "Jewelry planner: wedding guest, Rs 15,000.")
            page.set_input_files("input[name=outfit]", str(OUTFIT))
            page.click("button[type=submit]")
            page.wait_for_selector("#budget-totals")
            shot(page, "10_jewelry_results.png", "Jewelry picks with outfit image and sample-data tags.")
            page.goto(BASE + "/history", wait_until="networkidle")
            page.wait_for_timeout(400)
            shot(page, "11_history.png", "Session recommendation history.")
            page.goto(BASE + "/testimonials", wait_until="networkidle")
            shot(page, "12_testimonials.png", "User stories page.")
            page.goto(BASE + "/home-planner")
            page.fill("input[name=budget]", "100")
            page.click("button[type=submit]")
            page.wait_for_selector("#error-box")
            shot(page, "13_edge_budget_too_low.png", "Edge case: budget too low shows validation error.")
            page.goto(BASE + "/jewelry-planner")
            page.set_input_files("input[name=outfit]", {
                "name": "notes.txt",
                "mimeType": "text/plain",
                "buffer": b"hello",
            })
            page.click("button[type=submit]")
            page.wait_for_selector("#error-box")
            shot(page, "14_edge_invalid_image.png", "Edge case: non-image upload rejected.")
            page.goto(BASE + "/party-planner")
            page.click("button[type=submit]")
            page.wait_for_selector("#fallback-box, #budget-totals")
            shot(page, "15_edge_fallback.png", "Demo/fallback message with curated party list.")
            mobile = browser.new_page(viewport={"width": 390, "height": 844})
            mobile.goto(BASE, wait_until="networkidle")
            shot(mobile, "16_mobile_home.png", "Mobile landing 390x844.", True)
            mobile.goto(BASE + "/home-planner", wait_until="networkidle")
            shot(mobile, "17_mobile_home_planner.png", "Mobile home planner.", True)
            mobile.goto(BASE + "/party-planner")
            mobile.click("button[type=submit]")
            mobile.wait_for_selector("#budget-totals")
            shot(mobile, "18_mobile_party_results.png", "Mobile party results.", True)
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    (SHOT / "captions.json").write_text(json.dumps(captions, indent=2), encoding="utf-8")
    print("captions", len(captions))


if __name__ == "__main__":
    main()

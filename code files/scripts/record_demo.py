"""3–4 minute Playwright demo with caption overlays."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE_ROOT = Path(__file__).resolve().parent.parent   # "code files" folder
ROOT = CODE_ROOT.parent                              # repository root
MEDIA = ROOT / "media"
MEDIA.mkdir(exist_ok=True)
OUTFIT = CODE_ROOT / "pocketsmart" / "static" / "img" / "sample_outfit.png"
BASE = "http://127.0.0.1:5000"


def overlay(page, text: str):
    page.evaluate(
        """(t) => {
      let el = document.getElementById('cap');
      if (!el) {
        el = document.createElement('div');
        el.id = 'cap';
        el.style.cssText = 'position:fixed;bottom:12px;left:12px;right:12px;background:#134e4a;color:#fff;padding:10px 14px;z-index:9999;font:16px sans-serif;border-radius:8px;';
        document.body.appendChild(el);
      }
      el.textContent = t;
    }""",
        text,
    )


def main():
    proc = subprocess.Popen(
        [sys.executable, "-m", "pocketsmart.app"],
        cwd=str(CODE_ROOT),
        env={**os.environ, "GEMINI_API_KEY": "", "PYTHONPATH": str(CODE_ROOT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    time.sleep(1.2)
    raw = MEDIA / "demo_raw"
    raw.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(raw),
                record_video_size={"width": 1280, "height": 720},
            )
            page = ctx.new_page()
            page.goto(BASE)
            overlay(page, "PocketSmart AI — smart budget planner (Demo mode)")
            page.wait_for_timeout(8000)
            overlay(page, "Register a sample user to keep session history")
            page.goto(BASE + "/register")
            page.wait_for_timeout(4000)
            page.click("button[type=submit]")
            page.wait_for_timeout(4000)
            overlay(page, "Home planner: Rs 80,000 · living + kitchen + bedroom")
            page.goto(BASE + "/home-planner")
            page.wait_for_timeout(5000)
            page.click("button[type=submit]")
            page.wait_for_selector("#budget-totals")
            overlay(page, "Recommendations stay inside budget. Every card is sample data.")
            page.wait_for_timeout(12000)
            overlay(page, "Party planner: birthday, 40 guests, Rs 50,000")
            page.goto(BASE + "/party-planner")
            page.wait_for_timeout(5000)
            page.click("button[type=submit]")
            page.wait_for_selector("#budget-totals")
            overlay(page, "Budget split: catering, decoration, entertainment")
            page.wait_for_timeout(12000)
            overlay(page, "Jewelry: wedding guest, Rs 15,000 + outfit photo")
            page.goto(BASE + "/jewelry-planner")
            page.set_input_files("input[name=outfit]", str(OUTFIT))
            page.wait_for_timeout(4000)
            page.click("button[type=submit]")
            page.wait_for_selector("#budget-totals")
            overlay(page, "Outfit colours inform jewelry picks (sample Amazon/Flipkart)")
            page.wait_for_timeout(12000)
            overlay(page, "Session history stores recent plans")
            page.goto(BASE + "/history")
            page.wait_for_timeout(8000)
            overlay(page, "Edge case: budget too low")
            page.goto(BASE + "/home-planner")
            page.fill("input[name=budget]", "100")
            page.click("button[type=submit]")
            page.wait_for_selector("#error-box")
            page.wait_for_timeout(8000)
            overlay(page, "Thanks for watching PocketSmart AI")
            page.goto(BASE)
            page.wait_for_timeout(6000)
            ctx.close()
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    webm = next(raw.glob("*.webm"))
    mp4 = MEDIA / "Demo_Video.mp4"
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mp4)]
    )
    print("wrote", mp4, "size", mp4.stat().st_size)


if __name__ == "__main__":
    main()

"""Record live PocketSmart AI UI timed to voice clips d1–d10."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE_ROOT = Path(__file__).resolve().parent.parent   # "code files" folder
ROOT = CODE_ROOT.parent                              # repository root
OUTFIT = CODE_ROOT / "pocketsmart/static/img/sample_outfit.png"
RAW = ROOT / "media/demo_final_raw"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:5000"


def wait_ms(page, seconds: float, extra: float = 0.8):
    page.wait_for_timeout(int((seconds + extra) * 1000))


def main():
    # durations from ffmpeg
    d = {
        1: 11.26,
        2: 17.62,
        3: 20.69,
        4: 12.89,
        5: 16.01,
        6: 15.41,
        7: 12.10,
        8: 14.74,
        9: 14.86,
        10: 15.10,
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        page.goto(BASE, wait_until="networkidle")
        wait_ms(page, d[1])  # intro
        wait_ms(page, d[2])  # point at nav
        page.goto(BASE + "/home-planner", wait_until="networkidle")
        wait_ms(page, d[3])
        page.click("button[type=submit]")
        page.wait_for_selector("#budget-totals", timeout=15000)
        wait_ms(page, d[4] * 0.4)
        wait_ms(page, d[5])
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(1500)
        page.goto(BASE + "/party-planner", wait_until="networkidle")
        wait_ms(page, d[6])
        page.click("button[type=submit]")
        page.wait_for_selector("#budget-totals", timeout=15000)
        wait_ms(page, d[7] * 0.3)
        wait_ms(page, d[8])
        page.mouse.wheel(0, 350)
        page.wait_for_timeout(1200)
        page.goto(BASE + "/jewelry-planner", wait_until="networkidle")
        page.set_input_files("input[name=outfit]", str(OUTFIT))
        wait_ms(page, d[9])
        page.click("button[type=submit]")
        page.wait_for_selector("#budget-totals", timeout=15000)
        wait_ms(page, d[10])
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(4000)
        page.goto(BASE + "/history", wait_until="networkidle")
        page.wait_for_timeout(6000)
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(5000)
        ctx.close()
        browser.close()
    webm = next(RAW.glob("*.webm"))
    print("webm", webm)


if __name__ == "__main__":
    main()

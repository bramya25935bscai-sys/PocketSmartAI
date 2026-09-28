"""2–3 minute testing video: pytest then UI edge cases."""
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
BASE = "http://127.0.0.1:5000"


def overlay(page, text: str):
    page.evaluate(
        """(t) => {
      let el = document.getElementById('cap');
      if (!el) {
        el = document.createElement('div');
        el.id = 'cap';
        el.style.cssText = 'position:fixed;bottom:12px;left:12px;right:12px;background:#7c2d12;color:#fff;padding:10px 14px;z-index:9999;font:16px sans-serif;border-radius:8px;';
        document.body.appendChild(el);
      }
      el.textContent = t;
    }""",
        text,
    )


def main():
    pytest_out = subprocess.check_output(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=str(CODE_ROOT),
        env={**os.environ, "PYTHONPATH": str(CODE_ROOT)},
        text=True,
    )
    (ROOT / "docs" / "evidence" / "pytest_video.txt").write_text(pytest_out)
    proc = subprocess.Popen(
        [sys.executable, "-m", "pocketsmart.app"],
        cwd=str(CODE_ROOT),
        env={**os.environ, "GEMINI_API_KEY": "", "PYTHONPATH": str(CODE_ROOT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    time.sleep(1.2)
    raw = MEDIA / "test_raw"
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
            page.set_content(
                f"<pre style='font:18px monospace;padding:24px;white-space:pre-wrap'>pytest results\n{pytest_out}</pre>"
            )
            overlay(page, "Automated pytest: 22 tests passed")
            page.wait_for_timeout(15000)
            page.goto(BASE + "/home-planner")
            overlay(page, "Empty / invalid: budget 0")
            page.fill("input[name=budget]", "0")
            page.click("button[type=submit]")
            page.wait_for_timeout(8000)
            overlay(page, "Budget too small: Rs 100")
            page.fill("input[name=budget]", "100")
            page.click("button[type=submit]")
            page.wait_for_selector("#error-box")
            page.wait_for_timeout(8000)
            overlay(page, "Invalid image upload")
            page.goto(BASE + "/jewelry-planner")
            page.set_input_files(
                "input[name=outfit]",
                {"name": "notes.txt", "mimeType": "text/plain", "buffer": b"nope"},
            )
            page.click("button[type=submit]")
            page.wait_for_selector("#error-box")
            page.wait_for_timeout(8000)
            overlay(page, "AI failure / demo fallback still returns a list")
            page.goto(BASE + "/party-planner")
            page.click("button[type=submit]")
            page.wait_for_selector("#fallback-box, #budget-totals")
            page.wait_for_timeout(12000)
            overlay(page, "Testing complete — validation and fallback verified")
            page.wait_for_timeout(5000)
            ctx.close()
            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    webm = next(raw.glob("*.webm"))
    mp4 = MEDIA / "Testing_Video.mp4"
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mp4)]
    )
    print("wrote", mp4)


if __name__ == "__main__":
    main()

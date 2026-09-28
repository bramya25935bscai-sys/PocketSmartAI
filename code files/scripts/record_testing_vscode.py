"""Record testing demo starting from VS Code-like UI of REAL files + live pytest + live Flask UI."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE_ROOT = Path(__file__).resolve().parent.parent   # "code files" folder
ROOT = CODE_ROOT.parent                              # repository root
RAW = ROOT / "media" / "test_vscode_raw"
RAW.mkdir(parents=True, exist_ok=True)
HTML = ROOT / "media" / "vscode.html"
BASE = "http://127.0.0.1:5000"


def main():
    subprocess.check_call(
        ["python3", str(CODE_ROOT / "scripts" / "make_vscode_ui.py")],
        env={**os.environ, "PYTHONPATH": str(CODE_ROOT)},
    )
    # scene extra padding so total ~2.5 min (audio ~121s)
    pad = 4.0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until="networkidle")
        # t1 12.74 intro
        page.wait_for_timeout(int((12.74 + pad) * 1000))
        # t2 12.70 explorer
        page.wait_for_timeout(int((12.70 + pad) * 1000))
        # t3 14.18 test files
        page.click("#f-api")
        page.wait_for_timeout(int((14.18 + pad) * 1000))
        # t9 17.50 scroll cases
        page.evaluate("document.getElementById('code').scrollTop = 400")
        page.wait_for_timeout(6000)
        page.evaluate("document.getElementById('code').scrollTop = 900")
        page.wait_for_timeout(int((17.50 + pad - 6) * 1000))
        # t10 16.73 conftest / pytest.ini
        page.evaluate("window.showFile('conf','tests/conftest.py')")
        page.wait_for_timeout(8000)
        page.evaluate("window.showFile('ini','pytest.ini')")
        page.wait_for_timeout(int((16.73 + pad - 8) * 1000))
        page.evaluate("window.showFile('api','tests/test_api.py')")
        # t4 9.29 run command
        page.evaluate(
            "window.setTerm('user@vscode:~/PocketSmartAI$ python3 -m pytest tests -q\\n')"
        )
        page.wait_for_timeout(int((9.29 + 2) * 1000))
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests", "-q"],
            cwd=str(CODE_ROOT),
            env={**os.environ, "PYTHONPATH": str(CODE_ROOT)},
            capture_output=True,
            text=True,
        )
        out = (proc.stdout + "\n" + proc.stderr).strip()
        page.evaluate(
            """(t) => window.setTerm('user@vscode:~/PocketSmartAI$ python3 -m pytest tests -q\\n' + t + '\\nuser@vscode:~/PocketSmartAI$ ')""",
            out,
        )
        # t5 8.42 results
        page.wait_for_timeout(int((8.42 + pad) * 1000))
        # t6 9.89 explain
        page.wait_for_timeout(int((9.89 + pad) * 1000))
        # t7 UI validation
        page.goto(BASE + "/home-planner", wait_until="networkidle")
        page.wait_for_timeout(int((9.98 + 2) * 1000))
        page.fill("input[name=budget]", "100")
        page.click("button[type=submit]")
        page.wait_for_selector("#error-box", timeout=10000)
        # t8
        page.wait_for_timeout(int((9.77 + pad) * 1000))
        page.goto(HTML.as_uri())
        page.evaluate(
            """(t) => window.setTerm('user@vscode:~/PocketSmartAI$ python3 -m pytest tests -q\\n' + t)""",
            out,
        )
        page.wait_for_timeout(5000)
        ctx.close()
        browser.close()
    print("webm", next(RAW.glob("*.webm")))
    print("pytest", out[-200:])


if __name__ == "__main__":
    main()

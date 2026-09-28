"""Testing video: editor-like view of real tests, live pytest, live UI validation."""
from __future__ import annotations

import html
import os
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

CODE_ROOT = Path(__file__).resolve().parent.parent   # "code files" folder
ROOT = CODE_ROOT.parent                              # repository root
RAW = ROOT / "media/test_final_raw"
RAW.mkdir(parents=True, exist_ok=True)
TEST = (CODE_ROOT / "tests/test_api.py").read_text(encoding="utf-8")
CONF = (CODE_ROOT / "tests/conftest.py").read_text(encoding="utf-8")
TREE = subprocess.check_output(["find", str(CODE_ROOT / "tests"), "-name", "*.py"], text=True)

IDE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>PocketSmartAI — tests</title>
<style>
body{{margin:0;font-family:Consolas,monospace;background:#1e1e1e;color:#d4d4d4;display:flex;height:100vh}}
aside{{width:260px;background:#252526;padding:12px;border-right:1px solid #333}}
aside h1{{font:14px sans-serif;color:#ccc}}
main{{flex:1;overflow:auto;padding:16px}}
pre{{white-space:pre-wrap;font-size:15px;line-height:1.4}}
.tab{{background:#2d2d2d;padding:8px 12px;display:inline-block}}
.term{{background:#0c0c0c;color:#c6f6d5;padding:16px;min-height:280px;font-size:16px}}
</style></head>
<body>
<aside>
  <h1>EXPLORER</h1>
  <div>PocketSmartAI</div>
  <div>&nbsp;tests/</div>
  <div>&nbsp;&nbsp;conftest.py</div>
  <div>&nbsp;&nbsp;test_api.py</div>
  <div>&nbsp;pocketsmart/</div>
  <div>&nbsp;pytest.ini</div>
</aside>
<main>
  <div class="tab" id="tab">tests/test_api.py</div>
  <pre id="code">{html.escape(TEST[:4500])}</pre>
  <div class="tab">terminal</div>
  <pre class="term" id="term">user@host:~/PocketSmartAI$ </pre>
</main>
</body></html>
"""
(ROOT / "media/ide.html").write_text(IDE, encoding="utf-8")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = ctx.new_page()
        page.goto("file://" + str(ROOT / "media/ide.html"))
        page.wait_for_timeout(18000)  # intro + show files
        page.evaluate(
            """() => { document.getElementById('tab').textContent='tests/conftest.py';
            }"""
        )
        page.wait_for_timeout(4000)
        page.evaluate(
            """() => { document.getElementById('tab').textContent='tests/test_api.py'; }"""
        )
        page.wait_for_timeout(8000)
        page.evaluate(
            """() => { document.getElementById('term').textContent='user@host:~/PocketSmartAI$ python3 -m pytest tests -q\\n'; }"""
        )
        page.wait_for_timeout(3000)
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests", "-q"],
            cwd=str(CODE_ROOT),
            env={**os.environ, "PYTHONPATH": str(CODE_ROOT)},
            capture_output=True,
            text=True,
        )
        out = (proc.stdout + proc.stderr)[-2500:]
        page.evaluate(
            """(t) => { document.getElementById('term').textContent =
            'user@host:~/PocketSmartAI$ python3 -m pytest tests -q\\n' + t; }""",
            out,
        )
        page.wait_for_timeout(20000)
        page.goto("http://127.0.0.1:5000/home-planner", wait_until="networkidle")
        page.wait_for_timeout(8000)
        page.fill("input[name=budget]", "100")
        page.click("button[type=submit]")
        page.wait_for_selector("#error-box")
        page.wait_for_timeout(12000)
        page.goto("file://" + str(ROOT / "media/ide.html"))
        page.evaluate(
            """(t) => { document.getElementById('term').textContent =
            'user@host:~/PocketSmartAI$ python3 -m pytest tests -q\\n' + t; }""",
            out,
        )
        page.wait_for_timeout(10000)
        ctx.close()
        browser.close()
    print("webm", next(RAW.glob("*.webm")))


if __name__ == "__main__":
    main()

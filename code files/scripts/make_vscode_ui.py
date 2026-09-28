"""Generate a VS Code-like page using REAL project file contents."""
from pathlib import Path
import html

CODE_ROOT = Path(__file__).resolve().parent.parent   # "code files" folder
ROOT = CODE_ROOT.parent                              # repository root
OUT = ROOT / "media" / "vscode.html"

def load(rel, n=220):
    lines = (CODE_ROOT / rel).read_text(encoding="utf-8").splitlines()[:n]
    body = "\n".join(f"{i+1:>4}  {html.escape(line)}" for i, line in enumerate(lines))
    return body

api = load("tests/test_api.py", 180)
conf = load("tests/conftest.py", 80)
ini = load("pytest.ini", 20)

OUT.write_text(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>PocketSmartAI - Visual Studio Code</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;height:100%;font-family:'Segoe UI',Consolas,monospace;background:#1e1e1e;color:#cccccc}}
.win{{display:grid;grid-template-rows:32px 1fr 24px;height:100vh}}
.title{{background:#3c3c3c;display:flex;align-items:center;padding:0 12px;font-size:13px;color:#ddd}}
.title b{{margin-right:16px;color:#fff}}
.row{{display:grid;grid-template-columns:48px 260px 1fr;min-height:0}}
.act{{background:#333333;display:flex;flex-direction:column;align-items:center;padding-top:10px;gap:18px;color:#858585;font-size:18px}}
.act .on{{color:#fff}}
.side{{background:#252526;padding:10px 8px;overflow:auto;font-size:13px}}
.side h2{{font-size:11px;letter-spacing:1px;color:#bbb;margin:0 0 8px}}
.file{{padding:3px 8px;cursor:default;border-radius:3px}}
.file:hover,.file.sel{{background:#37373d}}
.folder{{color:#c5c5c5;margin-top:6px}}
.main{{display:flex;flex-direction:column;min-width:0;background:#1e1e1e}}
.tabs{{background:#252526;display:flex;font-size:13px}}
.tab{{padding:8px 14px;border-right:1px solid #1e1e1e}}
.tab.on{{background:#1e1e1e;color:#fff}}
pre{{margin:0;padding:12px 16px;overflow:auto;flex:1;font-size:14px;line-height:1.45;color:#d4d4d4}}
.termwrap{{height:220px;background:#0c0c0c;border-top:1px solid #333;display:flex;flex-direction:column}}
.termtabs{{font-size:12px;padding:6px 10px;background:#181818;color:#ccc}}
#term{{margin:0;padding:10px 14px;color:#d1ffd6;font-size:14px;overflow:auto;flex:1;white-space:pre-wrap}}
.status{{background:#007acc;color:#fff;font-size:12px;display:flex;justify-content:space-between;padding:0 10px;align-items:center}}
</style>
</head>
<body>
<div class="win">
  <div class="title"><b>Visual Studio Code</b> PocketSmartAI — tests/test_api.py</div>
  <div class="row">
    <div class="act"><span class="on">📁</span><span>🔍</span><span>🌿</span><span>▶</span></div>
    <div class="side">
      <h2>EXPLORER</h2>
      <div class="folder">POCKETSMARTAI</div>
      <div class="file">.env.example</div>
      <div class="file">README.md</div>
      <div class="file">pytest.ini</div>
      <div class="file">requirements.txt</div>
      <div class="folder">pocketsmart/</div>
      <div class="file">&nbsp;&nbsp;app.py</div>
      <div class="file">&nbsp;&nbsp;config.py</div>
      <div class="folder">tests/</div>
      <div class="file sel" id="f-api">&nbsp;&nbsp;test_api.py</div>
      <div class="file" id="f-conf">&nbsp;&nbsp;conftest.py</div>
      <div class="folder">scripts/</div>
      <div class="folder">docs/</div>
    </div>
    <div class="main">
      <div class="tabs">
        <div class="tab on" id="tabname">tests/test_api.py</div>
      </div>
      <pre id="code">{api}</pre>
      <div class="termwrap">
        <div class="termtabs">TERMINAL  bash</div>
        <pre id="term">user@vscode:~/PocketSmartAI$</pre>
      </div>
    </div>
  </div>
  <div class="status"><span>Python 3.13  |  UTF-8</span><span>PocketSmartAI  Ln 1, Col 1</span></div>
</div>
<script>
const files = {{
  api: `{api}`,
  conf: `{conf}`,
  ini: `{ini}`
}};
window.showFile = (key, title) => {{
  document.getElementById('code').textContent = files[key];
  document.getElementById('tabname').textContent = title;
  document.querySelector('.title').innerHTML = '<b>Visual Studio Code</b> PocketSmartAI — ' + title;
}};
window.setTerm = (t) => {{ document.getElementById('term').textContent = t; }};
</script>
</body>
</html>
""", encoding="utf-8")
print("wrote", OUT)

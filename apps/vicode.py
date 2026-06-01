# Demo utility: tiny web code workspace for /sd/vicode.
# Frontend is Preact + htm (served from /vendor/preact.js); backend API below.
from core.app import App
from core import input as ev
from core import display
import os

try:
    import json
except ImportError:
    json = None

ROOT = "/sd"                # browse the whole SD card
SEED_DIR = "/sd/vicode"     # default landing + where the demo files live
MAX_READ = 24000

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ViCode - pocketpython</title><style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#efe9da;--surface:#fff;--surface-soft:#f8f3e7;--primary:#f4856b;--primary-bright:#ff9d83;--primary-press:#db6c52;--ink:#1a1a1a;--muted:#8a8073;--border:#e6dfcd;--radius:14px;--radius-sm:10px;--radius-pill:999px;--shadow:0 1px 2px rgba(20,20,15,.04),0 4px 14px rgba(20,20,15,.06)}
*{box-sizing:border-box}
html,body,#app{height:100%}
body{margin:0;font-family:'Inter',-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased}
#app{display:grid;grid-template-rows:auto 1fr;height:100vh;height:100dvh}
.sideBtn{display:none;align-items:center;gap:.35rem;padding:.4rem .8rem;font-weight:600;background:var(--bg);color:var(--ink);border:0;border-radius:var(--radius-pill);font-size:.82rem;cursor:pointer}
.backdrop{display:none}
.top{padding:.85rem 1.1rem;border-bottom:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap}
.brand{display:flex;align-items:baseline;gap:.7rem}
.brand h1{font-size:1.65rem;font-weight:800;letter-spacing:-.025em;margin:0}
.brand .sub{color:var(--muted);font-size:.82rem;font-weight:500}
.tabs{display:flex;gap:.4rem}
.tabs a{padding:.35rem .8rem;background:var(--bg);color:var(--ink);text-decoration:none;font-weight:600;font-size:.82rem;border-radius:var(--radius-pill)}
.tabs a.on{background:var(--ink);color:var(--bg)}
.work{display:grid;grid-template-columns:280px 1fr;min-height:0}
.side{border-right:1px solid var(--border);background:var(--surface);padding:1rem;overflow:auto;min-height:0;display:flex;flex-direction:column;gap:.7rem}
.newbar{display:flex;gap:.4rem}
.newbar input{flex:1;min-width:0}
.crumb{font:12px ui-monospace,monospace;color:var(--muted);word-break:break-all}
.tree{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:.15rem;overflow:auto}
.row{display:grid;grid-template-columns:1fr auto;gap:.5rem;align-items:center;padding:.5rem .6rem;border-radius:var(--radius-sm);cursor:pointer;border:1px solid transparent}
.row:hover{background:var(--bg)}
.row.on{background:var(--ink);color:var(--bg)}
.row.on .nm,.row.on .sz{color:inherit}
.row.up .nm{color:var(--muted)}
.row .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:500}
.row.dir .nm{color:var(--primary);font-weight:600}
.row .sz{font:11px ui-monospace,monospace;color:var(--muted)}
.editor{display:grid;grid-template-rows:auto 1fr auto;min-width:0;min-height:0}
.ehead{display:flex;align-items:center;gap:.45rem;padding:.65rem .9rem;border-bottom:1px solid var(--border);background:var(--surface)}
.ehead .title{flex:1;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.95rem}
textarea{width:100%;height:100%;border:0;resize:none;padding:1rem 1.1rem;background:var(--surface-soft);color:var(--ink);font:14px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:2;outline:none}
.efoot{display:flex;justify-content:space-between;align-items:center;padding:.5rem .95rem;border-top:1px solid var(--border);background:var(--surface);color:var(--muted);font-size:.78rem}
.empty{display:grid;place-items:center;height:100%;text-align:center;color:var(--muted);background:var(--surface-soft);padding:1rem}
.empty .elogo{font-size:2.6rem;font-weight:800;color:var(--primary);letter-spacing:-.03em;margin-bottom:.3rem}
button{font:inherit;font-size:.85rem;font-weight:600;border:0;background:var(--bg);color:var(--ink);border-radius:var(--radius-pill);padding:.45rem .85rem;cursor:pointer;touch-action:manipulation;transition:opacity .12s,transform .05s}
button:hover{opacity:.85}
button:active{transform:scale(.97)}
button.primary{background:var(--primary);color:var(--ink)}
button.primary:hover{background:var(--primary-bright);opacity:1}
button.danger{background:#d75555;color:#fff}
input{font:inherit;font-size:.92rem;border:1px solid var(--border);border-radius:var(--radius-sm);padding:.5rem .7rem;background:#fff;color:var(--ink)}
input:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(244,133,107,.2)}
@media(max-width:760px){
  .top{padding:.5rem .75rem;gap:.5rem;flex-wrap:nowrap}
  .brand h1{font-size:1.2rem}
  .brand .sub{display:none}
  .tabs{gap:.85rem;font-size:.88rem}
  .sideBtn{display:inline-flex}
  .work{grid-template-columns:1fr}
  .side{position:fixed;top:0;bottom:0;left:0;width:min(80vw,300px);z-index:11;transform:translateX(-105%);transition:transform .22s ease;box-shadow:0 8px 30px rgba(40,30,20,.2);max-height:none;border-right:1px solid var(--border)}
  .side.open{transform:translateX(0)}
  .backdrop{display:block;position:fixed;inset:0;background:rgba(20,15,10,.32);z-index:10}
  .ehead{padding:.5rem .7rem;gap:.4rem}
  .ehead .title{font-size:.95rem}
  .ehead button{padding:.45rem .65rem;font-size:.85rem}
}
</style></head><body><div id="app"></div>
<script type="module">
import { html, render, useState, useEffect, useCallback } from '/vendor/preact.js';
const API='/app/vicode/';
const relJoin=(a,b)=>a?a+'/'+b:b;
const parent=p=>{const i=p.lastIndexOf('/');return i<0?'':p.slice(0,i);};
const baseName=p=>p.split('/').pop();
const NL=String.fromCharCode(10);
async function api(path,body){
  const opt=body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{};
  const j=await (await fetch(API+path,opt)).json();
  if(!j.ok) throw new Error(j.error||'error');
  return j;
}

function Tabs(){
  const t=[['/','Home'],['/files','Files'],['/admin','Settings'],['/app','Apps'],['/app/vicode/','ViCode']];
  return html`<nav class="tabs">${t.map(([h,l],i)=>
    html`<a href=${h} class=${i===4?'on':''}>${l}</a>`)}</nav>`;
}

function App(){
  const [cwd,setCwd]=useState('');
  const [entries,setEntries]=useState([]);
  const [cur,setCur]=useState('');
  const [text,setText]=useState('');
  const [dirty,setDirty]=useState(false);
  const [msg,setMsg]=useState('ready');
  const [nm,setNm]=useState('');
  const [sideOpen,setSideOpen]=useState(false);   // mobile drawer

  const list=useCallback(async (path)=>{
    try{ const j=await api('api/list?path='+encodeURIComponent(path)); setCwd(j.path); setEntries(j.entries); }
    catch(e){ setMsg(e.message); }
  },[]);
  useEffect(()=>{ list('vicode'); },[]);   // default landing

  const openFile=async (p)=>{
    try{ const j=await api('api/read?path='+encodeURIComponent(p)); setCur(j.path); setText(j.text); setDirty(false); setMsg('opened'); }
    catch(e){ setMsg(e.message); }
  };
  const onRow=(e)=>{
    const p=relJoin(cwd,e.name);
    if(e.type==='dir'){ list(p); }
    else { openFile(p); setSideOpen(false); }   // close drawer on mobile after opening a file
  };
  const save=async ()=>{
    if(!cur){ setMsg('no file selected'); return; }
    try{ const j=await api('api/write',{path:cur,text}); setDirty(false); setMsg('saved '+j.size+'b'); }
    catch(e){ setMsg(e.message); }
  };
  const newFile=async ()=>{
    const n=nm.trim(); if(!n) return;
    try{ const j=await api('api/newfile',{dir:cwd,name:n,text:'# '+n}); setNm(''); await list(cwd); openFile(j.path); }
    catch(e){ setMsg(e.message); }
  };
  const newDir=async ()=>{
    const n=nm.trim(); if(!n) return;
    try{ await api('api/newdir',{dir:cwd,name:n}); setNm(''); list(cwd); }
    catch(e){ setMsg(e.message); }
  };
  const del=async ()=>{
    if(!cur||!confirm('delete '+cur+'?')) return;
    try{ await api('api/delete',{path:cur}); setCur(''); setText(''); setMsg('deleted'); list(cwd); }
    catch(e){ setMsg(e.message); }
  };
  const rename=async ()=>{
    if(!cur) return;
    const n=prompt('rename to', baseName(cur)); if(!n) return;
    try{ const j=await api('api/rename',{path:cur,name:n}); setCur(j.path); setMsg('renamed'); list(cwd); }
    catch(e){ setMsg(e.message); }
  };

  return html`
    <header class="top">
      <button class="sideBtn" onClick=${()=>setSideOpen(s=>!s)}>Files</button>
      <div class="brand"><h1>ViCode</h1><span class="sub">/sd/vicode workspace</span></div>
      <${Tabs}/>
    </header>
    <main class="work">
      ${sideOpen?html`<div class="backdrop" onClick=${()=>setSideOpen(false)}></div>`:''}
      <aside class=${'side'+(sideOpen?' open':'')}>
        <div class="newbar">
          <input placeholder="new file or folder" value=${nm}
            onInput=${e=>setNm(e.target.value)}
            onKeyDown=${e=>{ if(e.key==='Enter') newFile(); }}/>
          <button onClick=${newFile} title="create file">+file</button>
          <button onClick=${newDir} title="create folder">+dir</button>
        </div>
        <div class="crumb">/sd/${cwd}</div>
        <ul class="tree">
          ${cwd?html`<li class="row up" onClick=${()=>list(parent(cwd))}><span class="nm">..</span><span class="sz"></span></li>`:''}
          ${entries.map(e=>html`
            <li class=${'row'+(e.type==='dir'?' dir':'')+(relJoin(cwd,e.name)===cur?' on':'')} onClick=${()=>onRow(e)}>
              <span class="nm">${e.name}${e.type==='dir'?'/':''}</span>
              <span class="sz">${e.size==null?'':e.size+'b'}</span>
            </li>`)}
        </ul>
      </aside>
      <section class="editor">
        ${cur?html`
          <div class="ehead">
            <span class="title">${cur}${dirty?' *':''}</span>
            <button onClick=${save} class="primary">Save</button>
            <button onClick=${rename}>Rename</button>
            <button onClick=${del} class="danger">Delete</button>
          </div>
          <textarea spellcheck="false" autocapitalize="off" autocorrect="off"
            autocomplete="off" value=${text}
            onInput=${e=>{ setText(e.target.value); setDirty(true); }}></textarea>
          <div class="efoot"><span>${msg}</span>
            <span>${text.length} chars - ${text.split(NL).length} lines</span></div>
        `:html`
          <div class="empty"><div>
            <div class="elogo">ViCode</div>
            <p>Pick a file on the left, or create one.</p>
            <p>${msg}</p>
          </div></div>
        `}
      </section>
    </main>`;
}
render(html`<${App}/>`, document.getElementById('app'));
</script></body></html>"""


def _json_load(body):
    if not json or not body:
        return {}
    try:
        if isinstance(body, bytes):
            body = body.decode()
        return json.loads(body)
    except Exception:
        return {}


def _is_dir(path):
    try:
        return (os.stat(path)[0] & 0x4000) != 0
    except OSError:
        return False


def _is_file(path):
    try:
        return (os.stat(path)[0] & 0x8000) != 0
    except OSError:
        return False


def _mkdir(path):
    try:
        os.mkdir(path)
    except OSError:
        pass


def _mkdirs(path):
    cur = ""
    for part in path.split("/"):
        if not part:
            continue
        cur += "/" + part
        _mkdir(cur)


def _clean_part(name):
    name = str(name or "").replace("\\", "/").strip()
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    bad = ('', '.', '..')
    if name in bad or "\x00" in name:
        return None
    return name[:48]


def _safe(rel):
    """Resolve a UI path (relative to /sd) to (clean_rel, absolute_path).
    Tolerates a leading /sd/ or sd/ prefix from clients that hand back full
    paths. Returns (None, None) if it would escape /sd via .. or nulls."""
    rel = str(rel or "").replace("\\", "/").strip()
    while rel.startswith("/"):
        rel = rel[1:]
    if rel.startswith("sd/"):
        rel = rel[3:]
    elif rel == "sd":
        rel = ""
    parts = []
    for part in rel.split("/"):
        if not part or part == ".":
            continue
        if part == ".." or "\x00" in part:
            return None, None
        parts.append(part)
    clean = "/".join(parts)
    return clean, ROOT + (("/" + clean) if clean else "")


def _rel_from_abs(path):
    if path == ROOT:
        return ""
    if path.startswith(ROOT + "/"):
        return path[len(ROOT) + 1:]
    return ""


def _write(path, text):
    if isinstance(text, bytes):
        data = text
    else:
        data = str(text).encode()
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def _seed():
    """Populate the default workspace under SEED_DIR. Idempotent: only writes
    files that don't exist yet, so we don't clobber user edits."""
    _mkdirs(SEED_DIR)
    samples = {
        SEED_DIR + "/README.md": "# ViCode\n\nWorkspace de teste no SD.\nEdita, guarda, cria pastas e brinca.\n",
        SEED_DIR + "/ideas.txt": "focus timer polish\npixel icons\nmini synth\n",
        SEED_DIR + "/scripts/hello.py": "print('hello from /sd/vicode')\n",
        SEED_DIR + "/notes/style_tokens.css": ":root {\n  --primary: #de5f30;\n  --surface: #fffdf8;\n  --border: #dfd2c3;\n}\n",
    }
    for path, text in samples.items():
        parent = path.rsplit("/", 1)[0]
        _mkdirs(parent)
        if not _is_file(path):
            _write(path, text)


def _list(rel):
    clean, path = _safe(rel)
    if path is None:
        return {"ok": False, "error": "bad path"}
    if not _is_dir(path):
        return {"ok": False, "error": "not a directory"}
    out = []
    for name in os.listdir(path):
        full = path.rstrip("/") + "/" + name
        try:
            st = os.stat(full)
            typ = "dir" if (st[0] & 0x4000) else "file"
            size = None if typ == "dir" else st[6]
        except OSError:
            typ = "unknown"
            size = None
        out.append({"name": name, "type": typ, "size": size})
    out.sort(key=lambda e: (0 if e["type"] == "dir" else 1, e["name"].lower()))
    return {"ok": True, "path": clean, "entries": out}


def _read(rel):
    clean, path = _safe(rel)
    if path is None:
        return {"ok": False, "error": "bad path"}
    if not _is_file(path):
        return {"ok": False, "error": "not a file"}
    size = os.stat(path)[6]
    if size > MAX_READ:
        return {"ok": False, "error": "file too large"}
    with open(path, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode()
    except Exception:
        return {"ok": False, "error": "not utf-8 text"}
    return {"ok": True, "path": clean, "text": text, "size": size}


class ViCode(App):
    name = "vicode"
    wants_screensaver = False

    def __init__(self):
        self._last = "vicode/README.md"
        self._msg = "workspace"
        self._count = 0

    def on_enter(self):
        try:
            _seed()
            self._count = len(os.listdir(ROOT))
        except Exception as e:
            self._msg = str(e)[:18]

    def on_input(self, e):
        if e == ev.SELECT:
            self._last = "vicode/README.md"
        elif e == ev.NAV_UP:
            self._last = "vicode/ideas.txt"
        elif e == ev.NAV_DOWN:
            self._last = "vicode/scripts/hello.py"

    def on_web(self, method, subpath, params, body):
        try:
            _seed()
            if subpath == "" or subpath is None:
                return _PAGE
            if subpath == "api/list":
                return _list(params.get("path", ""))
            if subpath == "api/read":
                res = _read(params.get("path", ""))
                if res.get("ok"):
                    self._last = res.get("path", self._last)
                    self._msg = "opened"
                return res
            data = _json_load(body)
            if subpath == "api/write":
                clean, path = _safe(data.get("path", ""))
                if path is None or not _is_file(path):
                    return {"ok": False, "error": "bad file"}
                size = _write(path, data.get("text", ""))
                self._last = clean
                self._msg = "saved"
                return {"ok": True, "path": clean, "size": size}
            if subpath == "api/newfile":
                dclean, dpath = _safe(data.get("dir", ""))
                name = _clean_part(data.get("name", ""))
                if dpath is None or name is None or not _is_dir(dpath):
                    return {"ok": False, "error": "bad name"}
                path = dpath.rstrip("/") + "/" + name
                if _is_file(path) or _is_dir(path):
                    return {"ok": False, "error": "exists"}
                _write(path, data.get("text", ""))
                clean = (dclean + "/" + name).strip("/")
                self._last = clean
                self._msg = "created"
                return {"ok": True, "path": clean}
            if subpath == "api/newdir":
                dclean, dpath = _safe(data.get("dir", ""))
                name = _clean_part(data.get("name", ""))
                if dpath is None or name is None or not _is_dir(dpath):
                    return {"ok": False, "error": "bad name"}
                _mkdir(dpath.rstrip("/") + "/" + name)
                return {"ok": True, "path": (dclean + "/" + name).strip("/")}
            if subpath == "api/delete":
                clean, path = _safe(data.get("path", ""))
                if path is None or path == ROOT:
                    return {"ok": False, "error": "bad path"}
                if _is_dir(path):
                    os.rmdir(path)
                elif _is_file(path):
                    os.remove(path)
                else:
                    return {"ok": False, "error": "not found"}
                self._msg = "deleted"
                return {"ok": True}
            if subpath == "api/rename":
                clean, path = _safe(data.get("path", ""))
                name = _clean_part(data.get("name", ""))
                if path is None or name is None or path == ROOT:
                    return {"ok": False, "error": "bad name"}
                new_path = path.rsplit("/", 1)[0] + "/" + name
                os.rename(path, new_path)
                self._last = (_rel_from_abs(new_path))
                self._msg = "renamed"
                return {"ok": True, "path": self._last}
            return {"ok": False, "error": "unknown action"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, lcd.color(246, 241, 232))
        hot = lcd.color(222, 95, 48)
        ink = lcd.color(29, 27, 24)
        line = lcd.color(180, 170, 156)
        display.text_scaled(lcd, "ViCode", 8, sb + 12, ink, scale=3)
        lcd.fb.hline(8, sb + 52, lcd.width - 16, ink)
        lcd.fb.fill_rect(12, sb + 76, 44, 44, hot)
        lcd.fb.rect(64, sb + 76, 44, 44, line)
        lcd.fb.rect(116, sb + 76, 44, 44, line)
        display.text_scaled(lcd, "SD workspace", 8, sb + 140, ink, scale=2)
        lcd.fb.text("/sd/vicode", 8, sb + 172, ink)
        lcd.fb.text(("last: " + self._last)[:20], 8, sb + 192, ink)
        lcd.fb.text(("state: " + self._msg)[:20], 8, sb + 208, ink)
        display.text_scaled(lcd, "/app/vicode", 8, lcd.height - 24, hot, scale=1)

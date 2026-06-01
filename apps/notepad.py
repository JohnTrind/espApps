# Demo utility: browser note pad mirrored on the LCD.
from core.app import App
from core import input as ev
from core import display

try:
    import json
except ImportError:
    json = None

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>notepad - pocketpython</title><style>
body{font-family:system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:1rem;max-width:520px;margin-left:auto;margin-right:auto}
a{color:#8ab4f8;text-decoration:none}h1{font-size:1.05rem;opacity:.75;font-weight:500;text-align:center}
textarea{box-sizing:border-box;width:100%;min-height:12rem;padding:.8rem;background:#1f1f1f;color:#eee;border:1px solid #444;border-radius:.45rem;font:1rem ui-monospace,monospace}
.row{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-top:.6rem}button{padding:1rem;background:#282828;color:#eee;border:1px solid #444;border-radius:.45rem;font:inherit}
#s{opacity:.7;text-align:center}
</style></head><body>
<a href="/app">&#8592; web apps</a><h1>notepad</h1><textarea id="note" maxlength="180"></textarea>
<div class="row"><button onclick="save()">save</button><button onclick="clearit()">clear</button></div><p id="s"></p>
<script>
async function load(){const j=await (await fetch('/app/notepad/state')).json();note.value=j.note;s.textContent=j.note.length+' chars'}
async function save(){const j=await (await fetch('/app/notepad/save',{method:'POST',body:JSON.stringify({note:note.value})})).json();s.textContent=j.note.length+' chars saved'}
async function clearit(){note.value='';await save()}
load();
</script></body></html>"""


def _payload(body):
    if not json or not body:
        return {}
    try:
        if isinstance(body, bytes):
            body = body.decode()
        return json.loads(body)
    except Exception:
        return {}


def _wrap(text, cols):
    out = []
    for raw in text.replace("\r", "").split("\n"):
        line = raw
        while len(line) > cols:
            out.append(line[:cols])
            line = line[cols:]
        out.append(line)
    return out


class Notepad(App):
    name = "notepad"

    def __init__(self):
        self._note = "hello from pocketpython"
        self._cursor = 0

    def _state(self):
        return {"ok": True, "note": self._note}

    def on_input(self, e):
        lines = _wrap(self._note, 20)
        if e == ev.NAV_UP:
            self._cursor = max(0, self._cursor - 1)
        elif e == ev.NAV_DOWN:
            self._cursor = min(max(0, len(lines) - 1), self._cursor + 1)
        elif e == ev.SELECT:
            self._note = ""
            self._cursor = 0

    def on_web(self, method, subpath, params, body):
        if subpath == "save":
            note = _payload(body).get("note", "")
            self._note = str(note)[:180]
            self._cursor = 0
        elif subpath not in ("", "state"):
            return {"ok": False, "error": "unknown action"}
        if subpath:
            return self._state()
        return _PAGE

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, 0)
        display.text_scaled(lcd, "notepad", 8, sb + 8, lcd.color(255, 220, 0), scale=2)
        lines = _wrap(self._note or "(empty)", 20)
        y = sb + 42
        for line in lines[self._cursor:self._cursor + 11]:
            lcd.fb.text(line[:20], 8, y, 0xFFFF)
            y += 14
        dim = lcd.color(120, 120, 120)
        display.text_scaled(lcd, "web edit / SEL clear", 8, lcd.height - 22, dim, scale=1)

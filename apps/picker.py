# Demo utility/fun: enter options in the browser, pick one on web or LCD.
from core.app import App
from core import input as ev
from core import display
import random

try:
    import json
except ImportError:
    json = None

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>picker - pocketpython</title><style>
body{font-family:system-ui,sans-serif;background:#151515;color:#eee;margin:0;padding:1rem;max-width:480px;margin-left:auto;margin-right:auto;text-align:center}
a{color:#8ab4f8;text-decoration:none}h1{font-size:1.05rem;opacity:.75;font-weight:500}
textarea{box-sizing:border-box;width:100%;min-height:9rem;padding:.8rem;background:#202020;color:#eee;border:1px solid #444;border-radius:.45rem;font:1rem ui-monospace,monospace}
button{width:100%;padding:1rem;margin-top:.55rem;background:#282828;color:#eee;border:1px solid #444;border-radius:.45rem;font:inherit}
#choice{font-size:1.8rem;margin:1rem 0;color:#ffd84a;min-height:2.4rem}
</style></head><body>
<a href="/app">&#8592; web apps</a><h1>picker</h1><div id="choice"></div>
<textarea id="opts"></textarea><button onclick="save()">save options</button><button onclick="pick()">pick one</button>
<script>
function draw(j){opts.value=(j.options||[]).join('\\n');choice.textContent=j.choice||''}
async function load(){draw(await (await fetch('/app/picker/state')).json())}
async function save(){draw(await (await fetch('/app/picker/options',{method:'POST',body:JSON.stringify({options:opts.value})})).json())}
async function pick(){draw(await (await fetch('/app/picker/pick')).json())}
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


class Picker(App):
    name = "picker"

    def __init__(self):
        self._options = ["pizza", "walk", "code", "music"]
        self._choice = ""

    def _pick(self):
        if self._options:
            self._choice = self._options[random.randint(0, len(self._options) - 1)]

    def _state(self):
        return {"ok": True, "options": self._options, "choice": self._choice}

    def on_input(self, e):
        if e == ev.SELECT:
            self._pick()
        elif e == ev.NAV_UP and self._options:
            self._options = self._options[-1:] + self._options[:-1]
        elif e == ev.NAV_DOWN and self._options:
            self._options = self._options[1:] + self._options[:1]

    def on_web(self, method, subpath, params, body):
        if subpath == "pick":
            self._pick()
        elif subpath == "options":
            raw = _payload(body).get("options", "")
            if isinstance(raw, list):
                opts = [str(x).strip() for x in raw]
            else:
                opts = [x.strip() for x in str(raw).replace("\r", "").split("\n")]
            self._options = [x[:24] for x in opts if x][:12]
            self._choice = ""
        elif subpath not in ("", "state"):
            return {"ok": False, "error": "unknown action"}
        if subpath:
            return self._state()
        return _PAGE

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, 0)
        display.text_scaled(lcd, "picker", 8, sb + 8, lcd.color(255, 220, 0), scale=2)
        if self._choice:
            display.text_scaled(lcd, "choice:", 8, sb + 52, lcd.color(160, 160, 160), scale=1)
            display.text_scaled(lcd, self._choice[:10], 8, sb + 76, 0xFFFF, scale=3)
        else:
            y = sb + 48
            for opt in self._options[:8]:
                lcd.fb.text("- " + opt[:18], 8, y, 0xFFFF)
                y += 16
        dim = lcd.color(120, 120, 120)
        display.text_scaled(lcd, "SEL pick", 8, lcd.height - 22, dim, scale=1)

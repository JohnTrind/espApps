# Demo utility: small focus/countdown timer with browser controls.
from core.app import App
from core import input as ev
from core import display

try:
    import json
except ImportError:
    json = None

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>focus timer - pocketpython</title><style>
body{font-family:system-ui,sans-serif;background:#141414;color:#eee;margin:0;padding:1rem;max-width:430px;margin-left:auto;margin-right:auto;text-align:center}
a{color:#8ab4f8;text-decoration:none}h1{font-size:1.05rem;opacity:.75;font-weight:500}
#time{font:700 4rem ui-monospace,monospace;margin:1rem 0}.g{display:grid;grid-template-columns:1fr 1fr;gap:.5rem}
button,input{font:inherit}button{padding:1rem;background:#262626;color:#eee;border:1px solid #444;border-radius:.45rem}
input{width:5rem;padding:.65rem;background:#202020;color:#eee;border:1px solid #444;border-radius:.35rem;text-align:center}.wide{grid-column:1/3}
</style></head><body>
<a href="/app">&#8592; web apps</a><h1>focus timer</h1><div id="time">25:00</div>
<p><input id="mins" type="number" min="1" max="120" value="25"> min</p>
<div class="g"><button onclick="act('start')">start</button><button onclick="act('pause')">pause</button>
<button onclick="act('reset')">reset</button><button onclick="setm()">set</button></div>
<script>
function draw(j){let s=Math.max(0,j.left|0),m=(s/60)|0,r=s%60;time.textContent=String(m).padStart(2,'0')+':'+String(r).padStart(2,'0');mins.value=j.minutes}
async function act(a){draw(await (await fetch('/app/focustimer/'+a)).json())}
async function setm(){draw(await (await fetch('/app/focustimer/set',{method:'POST',body:JSON.stringify({minutes:+mins.value||25})})).json())}
async function poll(){try{draw(await (await fetch('/app/focustimer/state')).json())}catch(e){}}
poll();setInterval(poll,1000);
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


class FocusTimer(App):
    name = "focustimer"
    wants_screensaver = False

    def __init__(self):
        self._minutes = 25
        self._left_ms = self._minutes * 60000
        self._running = False
        self._flash_ms = 0

    def _state(self):
        return {
            "ok": True,
            "minutes": self._minutes,
            "left": (self._left_ms + 999) // 1000,
            "running": self._running,
        }

    def _set_minutes(self, minutes):
        self._minutes = max(1, min(120, int(minutes)))
        self._left_ms = self._minutes * 60000
        self._running = False

    def on_input(self, e):
        if e == ev.SELECT:
            self._running = not self._running
        elif e == ev.NAV_UP:
            self._set_minutes(self._minutes + 5)
        elif e == ev.NAV_DOWN:
            self._set_minutes(max(1, self._minutes - 5))

    def on_tick(self, dt):
        if self._flash_ms > 0:
            self._flash_ms -= dt
        if not self._running:
            return
        self._left_ms -= dt
        if self._left_ms <= 0:
            self._left_ms = 0
            self._running = False
            self._flash_ms = 2500

    def on_web(self, method, subpath, params, body):
        if subpath == "start":
            if self._left_ms <= 0:
                self._left_ms = self._minutes * 60000
            self._running = True
        elif subpath == "pause":
            self._running = False
        elif subpath == "reset":
            self._left_ms = self._minutes * 60000
            self._running = False
        elif subpath == "set":
            self._set_minutes(_payload(body).get("minutes", self._minutes))
        elif subpath not in ("", "state"):
            return {"ok": False, "error": "unknown action"}
        if subpath:
            return self._state()
        return _PAGE

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        bg = lcd.color(80, 20, 20) if self._flash_ms > 0 else 0
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, bg)
        s = (self._left_ms + 999) // 1000
        text = "%02d:%02d" % (s // 60, s % 60)
        display.text_scaled(lcd, "focus", 8, sb + 18, lcd.color(255, 220, 0), scale=2)
        display.text_scaled(lcd, text, 8, sb + 74, 0xFFFF, scale=3)
        state = "running" if self._running else ("done" if s == 0 else "paused")
        display.text_scaled(lcd, state, 8, sb + 132, lcd.color(170, 170, 170), scale=2)
        dim = lcd.color(120, 120, 120)
        display.text_scaled(lcd, "SEL start/pause", 8, lcd.height - 36, dim, scale=1)
        display.text_scaled(lcd, "UP/DOWN minutes", 8, lcd.height - 22, dim, scale=1)

# Demo utility: tap tempo / tiny metronome. Flashes the LED gently on beats.
from core.app import App
from core import input as ev
from core import display, led
import time

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>tap tempo - pocketpython</title><style>
body{font-family:system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:1rem;max-width:420px;margin-left:auto;margin-right:auto;text-align:center}
a{color:#8ab4f8;text-decoration:none}h1{font-size:1.05rem;opacity:.75;font-weight:500}
#bpm{font:700 4rem ui-monospace,monospace;margin:1rem 0}.g{display:grid;grid-template-columns:1fr 1fr;gap:.5rem}
button{padding:1rem;background:#282828;color:#eee;border:1px solid #444;border-radius:.45rem;font:inherit}.wide{grid-column:1/3}
</style></head><body>
<a href="/app">&#8592; web apps</a><h1>tap tempo</h1><div id="bpm">120</div>
<div class="g"><button onclick="act('down')">-</button><button onclick="act('up')">+</button>
<button class="wide" onclick="act('tap')">tap</button><button onclick="act('toggle')">start/stop</button><button onclick="act('reset')">reset</button></div><p id="s"></p>
<script>
function draw(j){bpm.textContent=j.bpm;s.textContent=j.running?'running':'stopped'}
async function act(a){draw(await (await fetch('/app/taptempo/'+a)).json())}
async function poll(){try{draw(await (await fetch('/app/taptempo/state')).json())}catch(e){}}
poll();setInterval(poll,1500);
</script></body></html>"""


class TapTempo(App):
    name = "taptempo"
    wants_screensaver = False

    def __init__(self):
        self._bpm = 120
        self._running = False
        self._beat_ms = 0
        self._flash_ms = 0
        self._last_tap = 0

    def on_exit(self):
        led.off()

    def _state(self):
        return {"ok": True, "bpm": self._bpm, "running": self._running}

    def _tap(self):
        now = time.ticks_ms()
        if self._last_tap:
            diff = time.ticks_diff(now, self._last_tap)
            if 250 <= diff <= 2000:
                self._bpm = max(30, min(240, int(60000 // diff)))
        self._last_tap = now
        self._flash_ms = 90

    def on_input(self, e):
        if e == ev.SELECT:
            self._tap()
        elif e == ev.NAV_UP:
            self._bpm = min(240, self._bpm + 1)
        elif e == ev.NAV_DOWN:
            self._bpm = max(30, self._bpm - 1)
        elif e == ev.LONG_SELECT:
            self._running = not self._running

    def on_tick(self, dt):
        if self._flash_ms > 0:
            self._flash_ms -= dt
            if self._flash_ms <= 0:
                led.off()
        if not self._running:
            return
        self._beat_ms += dt
        period = 60000 // self._bpm
        if self._beat_ms >= period:
            self._beat_ms %= period
            self._flash_ms = 80
            led.set_color(20, 20, 20)

    def on_web(self, method, subpath, params, body):
        if subpath == "tap":
            self._tap()
        elif subpath == "up":
            self._bpm = min(240, self._bpm + 1)
        elif subpath == "down":
            self._bpm = max(30, self._bpm - 1)
        elif subpath == "toggle":
            self._running = not self._running
            self._beat_ms = 0
        elif subpath == "reset":
            self._bpm = 120
            self._running = False
        elif subpath not in ("", "state"):
            return {"ok": False, "error": "unknown action"}
        if subpath:
            return self._state()
        return _PAGE

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        bg = lcd.color(40, 40, 40) if self._flash_ms > 0 else 0
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, bg)
        display.text_scaled(lcd, "tap tempo", 8, sb + 18, lcd.color(255, 220, 0), scale=2)
        display.text_scaled(lcd, str(self._bpm), 18, sb + 78, 0xFFFF, scale=5)
        display.text_scaled(lcd, "BPM", 112, sb + 110, lcd.color(170, 170, 170), scale=2)
        state = "running" if self._running else "stopped"
        display.text_scaled(lcd, state, 8, sb + 166, lcd.color(170, 170, 170), scale=1)
        dim = lcd.color(120, 120, 120)
        display.text_scaled(lcd, "SEL tap UP/DOWN bpm", 8, lcd.height - 36, dim, scale=1)
        display.text_scaled(lcd, "LONG SEL run", 8, lcd.height - 22, dim, scale=1)

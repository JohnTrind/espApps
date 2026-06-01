# Demo/fun: an 8x8 pixel canvas controlled from the browser and shown on LCD.
from core.app import App
from core import input as ev
from core import display

try:
    import json
except ImportError:
    json = None

_PAL = [
    (0, 0, 0), (255, 255, 255), (240, 64, 64), (255, 190, 40),
    (80, 210, 90), (64, 170, 255), (180, 100, 255), (255, 95, 170),
]

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>pixelpad - pocketpython</title><style>
body{font-family:system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:1rem;max-width:430px;margin-left:auto;margin-right:auto;text-align:center}
a{color:#8ab4f8;text-decoration:none}h1{font-size:1.05rem;opacity:.75;font-weight:500}
#grid{display:grid;grid-template-columns:repeat(8,1fr);gap:3px;margin:1rem auto;max-width:360px}
.px{aspect-ratio:1;border:1px solid #333;background:#000;border-radius:.2rem}.pal{display:grid;grid-template-columns:repeat(4,1fr);gap:.45rem;margin:.7rem 0}
.sw{height:2.7rem;border:2px solid #333;border-radius:.35rem}.on{border-color:#eee}button{padding:.9rem 1rem;background:#282828;color:#eee;border:1px solid #444;border-radius:.45rem;font:inherit}
</style></head><body>
<a href="/app">&#8592; web apps</a><h1>pixelpad</h1><div id="grid"></div><div id="pal" class="pal"></div><button onclick="clearit()">clear</button>
<script>
const C=['#000','#fff','#f04040','#ffbe28','#50d25a','#40aaff','#b464ff','#ff5faa'];let cur=2, pix=[];
function draw(j){pix=j.pixels||Array(64).fill(0);grid.innerHTML='';pix.forEach((c,i)=>{let d=document.createElement('button');d.className='px';d.style.background=C[c];d.onclick=()=>setp(i);grid.appendChild(d);});}
function paldraw(){pal.innerHTML='';C.forEach((c,i)=>{let b=document.createElement('button');b.className='sw '+(i==cur?'on':'');b.style.background=c;b.onclick=()=>{cur=i;paldraw()};pal.appendChild(b);});}
async function setp(i){draw(await (await fetch('/app/pixelpad/set',{method:'POST',body:JSON.stringify({i:i,c:cur})})).json())}
async function clearit(){draw(await (await fetch('/app/pixelpad/clear')).json())}
async function load(){draw(await (await fetch('/app/pixelpad/state')).json());paldraw()}
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


class PixelPad(App):
    name = "pixelpad"

    def __init__(self):
        self._pix = [0] * 64
        for i in (9, 14, 18, 21, 27, 28, 35, 36, 42, 45, 49, 54):
            self._pix[i] = 5
        self._cursor = 0
        self._color = 2

    def _state(self):
        return {"ok": True, "pixels": self._pix, "color": self._color}

    def on_input(self, e):
        if e == ev.NAV_UP:
            self._color = (self._color + 1) % len(_PAL)
        elif e == ev.NAV_DOWN:
            self._cursor = (self._cursor + 1) % 64
        elif e == ev.SELECT:
            self._pix[self._cursor] = self._color

    def on_web(self, method, subpath, params, body):
        if subpath == "set":
            p = _payload(body)
            i = max(0, min(63, int(p.get("i", 0))))
            c = max(0, min(len(_PAL) - 1, int(p.get("c", 1))))
            self._pix[i] = c
        elif subpath == "clear":
            self._pix = [0] * 64
        elif subpath not in ("", "state"):
            return {"ok": False, "error": "unknown action"}
        if subpath:
            return self._state()
        return _PAGE

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, 0)
        display.text_scaled(lcd, "pixelpad", 8, sb + 8, lcd.color(255, 220, 0), scale=2)
        cell = 17
        ox = (lcd.width - cell * 8) // 2
        oy = sb + 44
        for y in range(8):
            for x in range(8):
                idx = y * 8 + x
                r, g, b = _PAL[self._pix[idx]]
                lcd.fb.fill_rect(ox + x * cell, oy + y * cell, cell - 2, cell - 2, lcd.color(r, g, b))
                if idx == self._cursor:
                    lcd.fb.rect(ox + x * cell, oy + y * cell, cell - 2, cell - 2, lcd.color(255, 220, 0))
        dim = lcd.color(120, 120, 120)
        display.text_scaled(lcd, "DOWN move UP color", 8, lcd.height - 36, dim, scale=1)
        display.text_scaled(lcd, "SELECT paint", 8, lcd.height - 22, dim, scale=1)

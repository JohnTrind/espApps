"""Internal CPU temperature meter.

The ESP32-S3 has a die-temperature sensor exposed via
`esp32.mcu_temperature()` (Celsius float). Older builds only expose
`esp32.raw_temperature()` in Fahrenheit -- the fallback converts.
"""
from core.app import App
from core import display

try:
    import esp32
except ImportError:
    esp32 = None


_PAGE = b"""<h1>Temperature</h1>
<section class="card" style="text-align:center">
  <div id="temp" style="font:800 4rem ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--primary);margin:.4rem 0;letter-spacing:-.03em">--</div>
  <p class="muted" style="margin:.2rem 0">internal CPU sensor</p>
</section>
<section class="card">
  <h2 style="margin:0 0 .5rem;font-size:.95rem">Last 30 readings</h2>
  <canvas id="chart" width="520" height="120" style="width:100%;height:120px;background:var(--bg);border-radius:.4rem"></canvas>
</section>
<script>
const $=id=>document.getElementById(id);
const hist=[];
function draw(){
  const c=$('chart'); const ctx=c.getContext('2d');
  const W=c.width, H=c.height;
  ctx.fillStyle=getComputedStyle(document.body).backgroundColor||'#ece7df';
  ctx.fillRect(0,0,W,H);
  if(hist.length<2) return;
  const min=Math.min(...hist)-1, max=Math.max(...hist)+1;
  const range=Math.max(0.5,max-min);
  ctx.strokeStyle='#df5830'; ctx.lineWidth=2; ctx.beginPath();
  hist.forEach((v,i)=>{
    const x=i/(hist.length-1)*W;
    const y=H-((v-min)/range)*H*0.85-H*0.075;
    if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.stroke();
}
async function tick(){
  try{
    const j=await (await fetch('/app/temperature/read')).json();
    if(j.ok && j.celsius!=null){
      $('temp').textContent=j.celsius.toFixed(1)+' C';
      hist.push(j.celsius);
      if(hist.length>30) hist.shift();
      draw();
    } else {$('temp').textContent='n/a';}
  }catch(e){}
}
tick();
setInterval(tick,2000);
</script>"""


def _read_celsius():
    if esp32 is None:
        return None
    if hasattr(esp32, "mcu_temperature"):
        try:
            return float(esp32.mcu_temperature())
        except Exception:
            pass
    if hasattr(esp32, "raw_temperature"):
        try:
            f = float(esp32.raw_temperature())
            return (f - 32) * 5.0 / 9.0
        except Exception:
            pass
    return None


class Temperature(App):
    name = "temperature"
    wants_screensaver = False

    def __init__(self):
        self._t = None

    def on_enter(self):
        self._t = _read_celsius()

    def on_input(self, e):
        pass

    def on_draw(self, lcd):
        lcd.fb.fill(0)
        display.text_scaled(lcd, "temp", 8, 14, lcd.color(220, 180, 90), scale=2)
        t = _read_celsius()
        if t is not None:
            self._t = t
            display.text_scaled(lcd, "%.1fC" % t, 8, 64, 0xFFFF, scale=3)
        else:
            display.text_scaled(lcd, "n/a", 8, 64, 0xFFFF, scale=3)
        lcd.fb.text("internal sensor", 8, lcd.height - 40,
                    lcd.color(150, 150, 150))

    def on_web(self, method, subpath, params, body):
        if subpath == "read":
            return {"ok": True, "celsius": _read_celsius()}
        from core import web_server
        return web_server.page("temperature", _PAGE)

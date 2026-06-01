"""Live meter for the 4 capacitive touch pads.

Hands /api/touch/snapshot-style data to the browser at ~3 Hz so you can
watch the readings drop below the threshold each time a finger lands.
Useful for calibrating THRESHOLD_RATIO in core/touch.py.
"""
from core.app import App
from core import display, touch


_PAGE = b"""<h1>Touch Meter</h1>
<section class="card">
  <p class="muted" style="margin:0 0 .6rem">Each bar shows the live capacitance reading vs. the baseline learned at boot. The bar turns orange while the pad is registered as touched.</p>
  <div id="pads" style="display:grid;gap:.6rem"></div>
</section>
<script>
const $=id=>document.getElementById(id);
async function tick(){
  try{
    const j=await (await fetch('/app/touchmeter/read')).json();
    const root=$('pads'); root.innerHTML='';
    (j.pads||[]).forEach(p=>{
      const card=document.createElement('div');
      card.style.cssText='padding:.5rem .7rem;border-radius:.5rem;background:var(--bg);border:1px solid var(--border)';
      const head=document.createElement('div');
      head.style.cssText='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.35rem';
      head.innerHTML='<span style="font-weight:600">GP'+p.gp+'</span><span class="note">'+p.read+' / base '+p.baseline+'  (thr '+p.threshold+')</span>';
      const bar=document.createElement('div');
      bar.style.cssText='height:14px;background:var(--surface);border-radius:.3rem;overflow:hidden;border:1px solid var(--border)';
      const fill=document.createElement('div');
      const pct=Math.max(0,Math.min(100,Math.round(100*p.read/Math.max(1,p.baseline))));
      fill.style.cssText='height:100%;width:'+pct+'%;background:'+(p.touched?'var(--primary)':'#8a847b')+';transition:width .1s ease,background .1s ease';
      bar.appendChild(fill);
      card.appendChild(head); card.appendChild(bar);
      root.appendChild(card);
    });
  }catch(e){}
}
tick();
setInterval(tick,300);
</script>"""


class TouchMeter(App):
    name = "touchmeter"
    wants_screensaver = False

    def on_input(self, e):
        pass

    def on_draw(self, lcd):
        lcd.fb.fill(0)
        display.text_scaled(lcd, "touch", 8, 14, lcd.color(220, 180, 90), scale=2)
        display.text_scaled(lcd, "meter", 8, 38, lcd.color(220, 220, 220), scale=2)
        snap = touch.snapshot()
        y = 70
        for p in snap:
            tag = "GP{}: {:>5}".format(p["gp"], p["read"])
            lcd.fb.text(tag, 8, y,
                        lcd.color(255, 120, 60) if p["touched"]
                        else lcd.color(220, 220, 220))
            y += 14
        lcd.fb.text("see /app/touchmeter/", 8, lcd.height - 40,
                    lcd.color(150, 150, 150))

    def on_web(self, method, subpath, params, body):
        if subpath == "read":
            return {"ok": True, "pads": touch.snapshot()}
        from core import web_server
        return web_server.page("touch meter", _PAGE)

"""WiFi radar: list nearby access points with their SSID, RSSI, channel
and security mode. The web view auto-refreshes every few seconds; the
LCD just shows the count + the strongest network's SSID at a glance.
"""
from core.app import App
from core import display, wifi_manager


_PAGE = b"""<h1>WiFi Radar</h1>
<section class="card">
  <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem">
    <p class="muted" id="status" style="flex:1;margin:0">scanning...</p>
    <button id="rescanBtn">Rescan</button>
  </div>
  <ul class="list" id="nets"></ul>
</section>
<script>
const $=id=>document.getElementById(id);
const SECS=['open','WEP','WPA','WPA2','WPA/WPA2','WPA2-ENT','WPA3','WPA2/WPA3'];
function bars(rssi){
  const s = rssi >= -55 ? 4 : rssi >= -68 ? 3 : rssi >= -80 ? 2 : rssi >= -90 ? 1 : 0;
  let out=''; for(let i=0;i<4;i++) out += i<s ? '|' : '.';
  return out;
}
async function scan(){
  $('status').textContent='scanning...';
  try{
    const j=await (await fetch('/app/wifiradar/scan')).json();
    const ul=$('nets'); ul.innerHTML='';
    const nets=(j.networks||[]);
    nets.forEach(n=>{
      const li=document.createElement('li');
      const left=document.createElement('span'); left.className='nm';
      left.textContent=n.ssid||'(hidden)';
      const right=document.createElement('span'); right.className='sz';
      right.textContent=bars(n.rssi)+' '+n.rssi+'dBm  ch'+n.channel+'  '+(SECS[n.security]||'?');
      li.appendChild(left); li.appendChild(right);
      ul.appendChild(li);
    });
    $('status').textContent=nets.length+' network'+(nets.length===1?'':'s');
  }catch(e){$('status').textContent='offline';}
}
$('rescanBtn').onclick=scan;
scan();
setInterval(scan,8000);
</script>"""


class WiFiRadar(App):
    name = "wifiradar"
    wants_screensaver = False

    def __init__(self):
        self._top = ""
        self._count = 0
        self._mark = 0

    def on_enter(self):
        self._mark = 0  # force a redraw

    def on_input(self, e):
        pass

    def on_draw(self, lcd):
        lcd.fb.fill(0)
        display.text_scaled(lcd, "wifi", 8, 14, lcd.color(220, 220, 220), scale=2)
        display.text_scaled(lcd, "radar", 8, 38, lcd.color(220, 180, 90), scale=2)
        lcd.fb.text("see /app/wifiradar/", 8, lcd.height - 40,
                    lcd.color(150, 150, 150))

    def on_web(self, method, subpath, params, body):
        if subpath == "scan":
            out = []
            for entry in wifi_manager.scan():
                try:
                    ssid = entry[0].decode() if isinstance(entry[0], bytes) else str(entry[0])
                except UnicodeError:
                    ssid = ""
                out.append({
                    "ssid": ssid,
                    "rssi": entry[3],
                    "channel": entry[2],
                    "security": entry[4],
                })
            return {"ok": True, "networks": out}
        from core import web_server
        return web_server.page("wifi radar", _PAGE)

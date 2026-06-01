"""Webhook notification receiver.

POST to /app/notify/in with JSON; the body lands in the frog's speech
bubble and a rolling log keeps the last 30 messages so you can browse
recent notifications on the web. Accepts the Home Assistant
`notify.<service>` payload shape `{title, message, data}` so HA can
post here directly via the REST notify integration.

A few accepted payload shapes:

    {"message": "hello"}                              -> "hello"
    {"title": "Build", "message": "OK"}               -> "Build: OK"
    {"text": "hi"}  or  {"body": "hi"}                -> "hi"
    "raw string"                                       -> "raw string"

Anything else gets json.dumps()'d.
"""
import time
from core.app import App
from core import display
from core import os as kernel

try:
    import json
except ImportError:
    json = None


_PAGE = b"""<h1>Notify</h1>
<section class="card">
  <h2>Test</h2>
  <form id="testForm" onsubmit="return testSend(event)">
    <label>Title <input name="title" type="text" maxlength="40" placeholder="optional"></label>
    <label>Message <input name="message" type="text" maxlength="200" required></label>
    <button type="submit" class="primary">Send</button>
    <span class="note" id="testMsg"></span>
  </form>
</section>

<section class="card">
  <h2>Webhook</h2>
  <p class="note" style="margin:0 0 .4rem">Anything on your LAN can POST JSON to this endpoint and the body lands on the frog's bubble.</p>
  <pre id="urlBox" style="background:var(--ink);color:var(--bg);padding:.7rem .9rem;border-radius:var(--radius-sm);font-size:.85rem;white-space:pre-wrap;word-break:break-all;margin:.3rem 0 0">POST http://&lt;ip&gt;/app/notify/in</pre>
  <p class="note" style="margin:.7rem 0 .3rem">Examples:</p>
  <pre style="background:var(--surface-soft);padding:.6rem .8rem;border-radius:var(--radius-sm);font-size:.78rem;overflow:auto;margin:0">curl -X POST http://HOST/app/notify/in \\
  -H "Content-Type: application/json" \\
  -d '{"title":"Build","message":"deploy ok"}'

# Home Assistant configuration.yaml:
notify:
  - platform: rest
    name: pocketpython
    resource: http://HOST/app/notify/in
    method: POST_JSON</pre>
</section>

<section class="card">
  <h2>Recent</h2>
  <ul class="list" id="log" style="margin:.3rem 0 0"></ul>
</section>
<script>
const $=id=>document.getElementById(id);
async function refresh(){
  try{
    const j=await (await fetch('/app/notify/state')).json();
    const ul=$('log'); ul.innerHTML='';
    if(!(j.recent||[]).length){
      ul.innerHTML='<li class="empty">no notifications yet</li>';
      return;
    }
    j.recent.slice().reverse().forEach(m=>{
      const li=document.createElement('li');
      const left=document.createElement('span'); left.className='nm';
      left.textContent=m.text;
      const right=document.createElement('span'); right.className='sz';
      right.textContent=m.ago+'s ago';
      li.appendChild(left); li.appendChild(right);
      ul.appendChild(li);
    });
  }catch(e){}
}
async function testSend(ev){
  ev.preventDefault();
  const f=ev.target;
  const body={message:f.message.value};
  if(f.title.value) body.title=f.title.value;
  const j=await (await fetch('/app/notify/in',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
  $('testMsg').textContent=j.ok?'sent':('error: '+(j.error||'?'));
  setTimeout(()=>$('testMsg').textContent='',2000);
  f.message.value='';
  refresh();
}
const u=$('urlBox');
u.textContent=u.textContent.replace('<ip>',location.host);
refresh();
setInterval(refresh,4000);
</script>"""


def _parse_payload(data):
    """Pull a (title, message) tuple out of the body, however it's shaped."""
    if isinstance(data, str):
        return None, data.strip() or "(empty)"
    if isinstance(data, dict):
        title = data.get("title") or data.get("subject")
        msg = (data.get("message") or data.get("text") or data.get("body")
               or data.get("msg"))
        if msg is None:
            # last resort: stringify the whole dict
            msg = json.dumps(data) if json else str(data)
        return (str(title) if title is not None else None,
                str(msg))
    return None, str(data) if data is not None else "(empty)"


class Notify(App):
    name = "notify"
    wants_screensaver = False

    def __init__(self):
        self._log = []           # list of {"text", "title", "t"}
        self._count = 0

    def on_input(self, e):
        pass

    def on_draw(self, lcd):
        lcd.fb.fill(0)
        display.text_scaled(lcd, "notify", 8, 14, lcd.color(220, 220, 220),
                            scale=2)
        lcd.fb.text("received: {}".format(self._count), 8, 50,
                    lcd.color(180, 180, 100))
        if self._log:
            last = self._log[-1]["text"][:21]
            lcd.fb.text("last:", 8, 76, lcd.color(150, 200, 250))
            lcd.fb.text(last, 8, 92, lcd.color(220, 220, 220))
        lcd.fb.text("POST /app/notify/in", 8, lcd.height - 40,
                    lcd.color(150, 150, 150))

    def on_web(self, method, subpath, params, body):
        if subpath == "in" and method == "POST":
            return self._receive(body)
        if subpath == "state":
            now = time.ticks_ms()
            return {"ok": True, "count": self._count, "recent": [{
                "text": e["text"],
                "ago": int(time.ticks_diff(now, e["t"]) / 1000),
            } for e in self._log]}
        from core import web_server
        return web_server.page("notify", _PAGE)

    # ---- internals ----------------------------------------------------

    def _receive(self, body):
        data = None
        if body:
            try:
                if isinstance(body, bytes):
                    body = body.decode()
                if body.strip().startswith(("{", "[")):
                    data = json.loads(body) if json else None
                else:
                    data = body
            except (ValueError, AttributeError):
                data = body
        title, message = _parse_payload(data)
        text = "{}: {}".format(title, message) if title else message
        text = text[:120]
        self._log.append({"text": text, "title": title, "t": time.ticks_ms()})
        if len(self._log) > 30:
            self._log.pop(0)
        self._count += 1

        # push to the frog bubble if it's loaded
        frog = kernel.app("frog")
        if frog is not None and hasattr(frog, "push"):
            try:
                frog.push(text)
            except Exception as e:
                print("[notify] frog push failed:", e)
        return {"ok": True, "text": text}

"""LAN-only chat -- no auth, no internet, in-memory message log.

Anyone on the same WiFi (or joined to the device's AP) can open
/app/localchat/, pick a name, and post messages. Pollers fetch the
delta since their last seen id every couple of seconds.

State lives in RAM only; reboot wipes the log. A small footer on the
LCD shows the last message + count.
"""
import time
from core.app import App
from core import display

try:
    import json
except ImportError:
    json = None


MAX_MESSAGES = 200
MAX_TEXT = 200
MAX_NAME = 16


_PAGE = b"""<h1>Local chat</h1>
<section class="card" style="display:flex;flex-direction:column;gap:.6rem">
  <label>Your name
    <input id="nameIn" maxlength="16" placeholder="anon">
  </label>
  <ul class="list" id="log" style="margin:0;max-height:50vh;overflow-y:auto"></ul>
  <form id="sendForm" onsubmit="return send(event)" style="display:flex;gap:.4rem">
    <input id="textIn" maxlength="200" placeholder="say something..." required style="flex:1">
    <button class="primary" type="submit">Send</button>
  </form>
  <p class="note" id="status" style="margin:0">connecting...</p>
</section>
<script>
const $=id=>document.getElementById(id);
let lastId=0;
let sending=false;
let polling=false;
const seen=new Set();
const NAME_KEY='localchat-name';
$('nameIn').value=localStorage.getItem(NAME_KEY)||'';
$('nameIn').addEventListener('change',()=>localStorage.setItem(NAME_KEY,$('nameIn').value.trim()));

function fmt(ms){
  const s=Math.max(0,Math.floor(ms/1000));
  if(s<60) return s+'s';
  if(s<3600) return Math.floor(s/60)+'m';
  return Math.floor(s/3600)+'h';
}
async function poll(){
  if(polling) return;
  polling=true;
  try{
    const j=await (await fetch('/app/localchat/messages?since='+lastId)).json();
    const ul=$('log');
    let added=0;
    (j.messages||[]).forEach(m=>{
      if(seen.has(m.id)) return;
      seen.add(m.id);
      const li=document.createElement('li');
      const left=document.createElement('span'); left.className='nm';
      const u=document.createElement('b'); u.textContent=m.user+': '; u.style.fontWeight='700';
      left.appendChild(u);
      left.appendChild(document.createTextNode(m.text));
      const right=document.createElement('span'); right.className='sz';
      right.textContent=fmt(j.now-m.t);
      li.appendChild(left); li.appendChild(right);
      ul.appendChild(li);
      lastId=Math.max(lastId,m.id);
      added++;
    });
    if(added){ ul.scrollTop=ul.scrollHeight; }
    $('status').textContent=j.count+' message'+(j.count===1?'':'s');
  }catch(e){ $('status').textContent='offline'; }
  finally{ polling=false; }
}
async function send(ev){
  ev.preventDefault();
  if(sending) return false;
  const text=$('textIn').value.trim();
  if(!text) return false;
  const user=$('nameIn').value.trim()||'anon';
  sending=true;
  $('textIn').disabled=true;
  try{
    const j=await (await fetch('/app/localchat/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user,text})})).json();
    if(j.ok){
      $('textIn').value='';
    } else {
      $('status').textContent='error: '+(j.error||'?');
    }
  }catch(e){ $('status').textContent='offline'; }
  finally{
    sending=false;
    $('textIn').disabled=false;
    $('textIn').focus();
    poll();
  }
  return false;
}
poll();
setInterval(poll,2500);
</script>"""


class LocalChat(App):
    name = "localchat"
    wants_screensaver = False

    def __init__(self):
        self._messages = []      # list of {id, user, text, t}
        self._next_id = 1

    def on_input(self, e):
        pass

    def on_draw(self, lcd):
        lcd.fb.fill(0)
        display.text_scaled(lcd, "chat", 8, 14, lcd.color(150, 200, 250),
                            scale=2)
        lcd.fb.text("messages: {}".format(len(self._messages)), 8, 50,
                    lcd.color(180, 180, 100))
        y = 78
        for m in self._messages[-4:]:
            user = m["user"][:6]
            line = "{}: {}".format(user, m["text"])[:24]
            lcd.fb.text(line, 8, y, lcd.color(220, 220, 220))
            y += 14
        lcd.fb.text("see /app/localchat/", 8, lcd.height - 40,
                    lcd.color(150, 150, 150))

    def on_web(self, method, subpath, params, body):
        if subpath == "messages":
            try:
                since = int(params.get("since", "0"))
            except (ValueError, TypeError):
                since = 0
            now = time.ticks_ms()
            new = [self._public(m, now) for m in self._messages
                   if m["id"] > since]
            return {
                "ok": True,
                "messages": new,
                "count": len(self._messages),
                "now": now,
            }
        if subpath == "post" and method == "POST":
            return self._post(body)
        from core import web_server
        return web_server.page("local chat", _PAGE)

    # ---- internals ----------------------------------------------------

    def _public(self, m, now):
        return {
            "id": m["id"],
            "user": m["user"],
            "text": m["text"],
            "t": m["t"],
        }

    def _post(self, body):
        if json is None or not body:
            return {"ok": False, "error": "no body"}
        try:
            if isinstance(body, bytes):
                body = body.decode()
            data = json.loads(body)
        except (ValueError, AttributeError):
            return {"ok": False, "error": "bad json"}
        if not isinstance(data, dict):
            return {"ok": False, "error": "bad json"}
        user = str(data.get("user", "")).strip()[:MAX_NAME] or "anon"
        text = str(data.get("text", "")).strip()[:MAX_TEXT]
        if not text:
            return {"ok": False, "error": "empty"}
        m = {"id": self._next_id, "user": user, "text": text,
             "t": time.ticks_ms()}
        self._next_id += 1
        self._messages.append(m)
        if len(self._messages) > MAX_MESSAGES:
            self._messages = self._messages[-MAX_MESSAGES:]
        return {"ok": True, "id": m["id"]}

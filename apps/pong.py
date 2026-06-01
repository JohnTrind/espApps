# Pong: UP/DOWN nudge your paddle, SELECT serves. First to 7 wins.
# Each press gives a few frames of momentum so motion feels smooth despite
# event-only input.
import random
from core.app import App
from core import input as ev
from core import display, led


PAD_W = 4
PAD_H = 32
PAD_SPEED = 4
BALL_R = 3
SERVE_VX = 3.5
MAX_SCORE = 7
FUEL_PER_TAP = 7        # frames of motion per UP/DOWN press


_PAGE = b"""<h1>Pong</h1>
<section class="card"><div id="root"></div></section>
<script type="module">
import { html, render, useState, useEffect, useRef } from '/vendor/preact.js';
const MAX=7;
function Game(){
  const cvRef=useRef(null);
  const moveRef=useRef(0);
  const ctlRef=useRef({serve:()=>{},restart:()=>{}});
  const [hud,setHud]=useState({you:0,cpu:0,waiting:true,winner:null});
  useEffect(()=>{
    const cv=cvRef.current, ctx=cv.getContext('2d');
    const W=cv.width, H=cv.height;
    const PW=6, PH=46, BR=4;
    let py,ay,bx,by,vx,vy,you,cpu,waiting,winner,serveDir;
    function park(){bx=W/2; by=H/2; vx=0; vy=0; waiting=true;}
    function reset(){
      py=H/2; ay=H/2; you=0; cpu=0; winner=null;
      serveDir=Math.random()<0.5?-1:1;
      park();
      setHud({you,cpu,waiting:true,winner:null});
    }
    function serve(){
      if(!waiting||winner)return;
      vx=4*serveDir;
      vy=(Math.random()*3-1.5);
      waiting=false;
      setHud(s=>({...s,waiting:false}));
    }
    function point(scoredBy){
      if(scoredBy==='you'){you++; serveDir=1;} else {cpu++; serveDir=-1;}
      if(you>=MAX) winner='you';
      else if(cpu>=MAX) winner='cpu';
      else park();
      setHud({you,cpu,waiting:!winner,winner});
    }
    ctlRef.current={serve, restart:reset};
    const onKey=e=>{
      if(e.key==='ArrowUp'){moveRef.current=-1; e.preventDefault();}
      else if(e.key==='ArrowDown'){moveRef.current=1; e.preventDefault();}
      else if(e.code==='Space'||e.key==='Enter'){
        if(winner) reset(); else serve();
      }
    };
    const onKeyUp=e=>{
      if((e.key==='ArrowUp'&&moveRef.current<0)||(e.key==='ArrowDown'&&moveRef.current>0)) moveRef.current=0;
    };
    window.addEventListener('keydown',onKey);
    window.addEventListener('keyup',onKeyUp);
    let raf=0;
    function loop(){
      py += moveRef.current * 5;
      py = Math.max(PH/2, Math.min(H-PH/2, py));
      if(!waiting && !winner){
        bx += vx; by += vy;
        if(by-BR<0){by=BR; vy=-vy;}
        else if(by+BR>H){by=H-BR; vy=-vy;}
        if(vx<0 && bx-BR<10+PW && bx+BR>10 && by>py-PH/2-BR && by<py+PH/2+BR){
          vx=Math.abs(vx)*1.06;
          vy += (by-py)/(PH/2);
          bx=10+PW+BR;
        }
        const ax=W-10-PW;
        if(vx>0 && bx+BR>ax && bx-BR<ax+PW && by>ay-PH/2-BR && by<ay+PH/2+BR){
          vx=-Math.abs(vx)*1.06;
          vy += (by-ay)/(PH/2);
          bx=ax-BR;
        }
        if(vx>0){
          if(ay<by-4) ay+=3.4;
          else if(ay>by+4) ay-=3.4;
        } else {
          if(ay<H/2-2) ay+=1; else if(ay>H/2+2) ay-=1;
        }
        ay = Math.max(PH/2, Math.min(H-PH/2, ay));
        if(bx<-BR) point('cpu');
        else if(bx>W+BR) point('you');
      }
      ctx.fillStyle='#181d2e'; ctx.fillRect(0,0,W,H);
      ctx.fillStyle='#3a4068';
      for(let y=0;y<H;y+=10) ctx.fillRect(W/2-1,y,2,5);
      ctx.fillStyle='#f4c100'; ctx.fillRect(10, py-PH/2, PW, PH);
      ctx.fillStyle='#8cc8ff'; ctx.fillRect(W-10-PW, ay-PH/2, PW, PH);
      if(!waiting && !winner){
        ctx.fillStyle='#fff';
        ctx.fillRect(bx-BR, by-BR, BR*2, BR*2);
      }
      raf=requestAnimationFrame(loop);
    }
    reset(); loop();
    return ()=>{cancelAnimationFrame(raf); window.removeEventListener('keydown',onKey); window.removeEventListener('keyup',onKeyUp);};
  },[]);
  const hold=v=>({
    onPointerDown:e=>{e.preventDefault(); try{e.target.setPointerCapture(e.pointerId);}catch(_){} moveRef.current=v;},
    onPointerUp:()=>{moveRef.current=0;},
    onPointerCancel:()=>{moveRef.current=0;},
    onPointerLeave:()=>{moveRef.current=0;},
  });
  return html`
    <canvas ref=${cvRef} width="480" height="280"
      style="max-width:100%;width:100%;height:auto;border-radius:.55rem;display:block;margin:0 auto;background:#181d2e"/>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.7rem">
      <span style="font:800 1.7rem ui-monospace,monospace;color:#f4c100">${hud.you}</span>
      <span class="muted">first to ${MAX}</span>
      <span style="font:800 1.7rem ui-monospace,monospace;color:#8cc8ff">${hud.cpu}</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-top:.7rem">
      <button style="padding:1.1rem;font-size:1.05rem;touch-action:none;user-select:none" ...${hold(-1)}>UP</button>
      <button style="padding:1.1rem;font-size:1.05rem;touch-action:none;user-select:none" ...${hold(1)}>DOWN</button>
    </div>
    ${hud.winner ? html`<button class="primary" style="width:100%;margin-top:.6rem" onClick=${()=>ctlRef.current.restart()}>${hud.winner==='you'?'You win - play again':'CPU wins - try again'}</button>`
      : hud.waiting ? html`<button class="primary" style="width:100%;margin-top:.6rem" onClick=${()=>ctlRef.current.serve()}>Serve</button>` : ''}
    <p class="muted" style="margin:.5rem 0 0;text-align:center;font-size:.82rem">Hold UP / DOWN (or arrow keys). Space to serve.</p>
  `;
}
render(html`<${Game}/>`, document.getElementById('root'));
</script>"""


class Pong(App):
    name = "pong"
    wants_screensaver = False

    def __init__(self):
        self._w = 320
        self._h = 150
        self._reset_full()

    def _reset_full(self):
        self._py = self._h // 2
        self._ay = self._h // 2
        self._ps = 0
        self._as = 0
        self._winner = None
        self._serve_dir = random.choice((-1, 1))
        self._fuel_up = 0
        self._fuel_dn = 0
        self._flash = 0
        self._park_ball()

    def _park_ball(self):
        self._bx = self._w / 2.0
        self._by = self._h / 2.0
        self._vx = 0.0
        self._vy = 0.0
        self._waiting = True

    def _serve(self):
        self._bx = self._w / 2.0
        self._by = self._h / 2.0
        self._vx = SERVE_VX * self._serve_dir
        self._vy = random.choice((-1.6, -1.0, 1.0, 1.6))
        self._waiting = False

    def on_enter(self):
        self._w = display.width()
        self._h = display.height() - display.ip_bar_height()
        self._reset_full()
        led.off()

    def on_exit(self):
        led.off()

    def on_input(self, e):
        if self._winner is not None:
            if e == ev.SELECT:
                self._reset_full()
            return
        if e == ev.NAV_UP:
            self._fuel_up += FUEL_PER_TAP
        elif e == ev.NAV_DOWN:
            self._fuel_dn += FUEL_PER_TAP
        elif e == ev.SELECT and self._waiting:
            self._serve()

    def _clamp_paddle(self, y):
        half = PAD_H // 2
        return max(half, min(self._h - half, y))

    def on_tick(self, dt):
        if self._flash > 0:
            self._flash -= 1
            if self._flash <= 0:
                led.off()
        if self._winner is not None:
            return

        # paddle momentum: up wins ties (rare)
        if self._fuel_up > 0:
            self._py -= PAD_SPEED
            self._fuel_up -= 1
        elif self._fuel_dn > 0:
            self._py += PAD_SPEED
            self._fuel_dn -= 1
        self._py = self._clamp_paddle(self._py)

        if self._waiting:
            return

        self._bx += self._vx
        self._by += self._vy
        if self._by - BALL_R < 0:
            self._by = BALL_R
            self._vy = -self._vy
        elif self._by + BALL_R > self._h:
            self._by = self._h - BALL_R
            self._vy = -self._vy

        # player paddle (left)
        px = 4
        if (self._vx < 0
                and self._bx - BALL_R < px + PAD_W
                and self._bx + BALL_R > px
                and self._by > self._py - PAD_H // 2 - BALL_R
                and self._by < self._py + PAD_H // 2 + BALL_R):
            self._vx = abs(self._vx) * 1.06
            offset = (self._by - self._py) / (PAD_H / 2.0)
            self._vy += offset * 1.1
            self._bx = px + PAD_W + BALL_R

        # cpu paddle (right)
        ax = self._w - 4 - PAD_W
        if (self._vx > 0
                and self._bx + BALL_R > ax
                and self._bx - BALL_R < ax + PAD_W
                and self._by > self._ay - PAD_H // 2 - BALL_R
                and self._by < self._ay + PAD_H // 2 + BALL_R):
            self._vx = -abs(self._vx) * 1.06
            offset = (self._by - self._ay) / (PAD_H / 2.0)
            self._vy += offset * 1.1
            self._bx = ax - BALL_R

        # cpu tracks ball with some lag + a small dead-zone
        ai_speed = 3
        if self._vx > 0:        # only chase when ball is coming toward CPU
            if self._ay < self._by - 4:
                self._ay += ai_speed
            elif self._ay > self._by + 4:
                self._ay -= ai_speed
        else:                   # drift toward center otherwise
            mid = self._h // 2
            if self._ay < mid - 2: self._ay += 1
            elif self._ay > mid + 2: self._ay -= 1
        self._ay = self._clamp_paddle(self._ay)

        # score
        if self._bx < -BALL_R:
            self._as += 1
            self._after_point(-1, False)
        elif self._bx > self._w + BALL_R:
            self._ps += 1
            self._after_point(1, True)

    def _after_point(self, serve_dir, player_scored):
        if player_scored:
            led.set_color(0, 24, 0)
        else:
            led.set_color(24, 0, 0)
        self._flash = 12
        if self._ps >= MAX_SCORE:
            self._winner = "you"
        elif self._as >= MAX_SCORE:
            self._winner = "cpu"
        else:
            self._serve_dir = serve_dir
            self._park_ball()

    def on_web(self, method, subpath, params, body):
        from core import web_server
        return web_server.page("pong", _PAGE)

    def on_draw(self, lcd):
        lcd.fb.fill(lcd.color(18, 20, 32))
        # net
        for y in range(0, self._h, 8):
            lcd.fb.fill_rect(self._w // 2 - 1, y, 2, 4, lcd.color(70, 70, 90))
        # paddles
        you_c = lcd.color(255, 220, 0)
        cpu_c = lcd.color(140, 200, 255)
        py = int(self._py)
        ay = int(self._ay)
        lcd.fb.fill_rect(4, py - PAD_H // 2, PAD_W, PAD_H, you_c)
        lcd.fb.fill_rect(self._w - 4 - PAD_W, ay - PAD_H // 2, PAD_W, PAD_H, cpu_c)
        # ball
        if not self._waiting and self._winner is None:
            bx, by = int(self._bx), int(self._by)
            lcd.fb.fill_rect(bx - BALL_R, by - BALL_R, BALL_R * 2, BALL_R * 2, 0xFFFF)
        # score
        display.text_scaled(lcd, str(self._ps), self._w // 2 - 40, 6, you_c, scale=3)
        display.text_scaled(lcd, str(self._as), self._w // 2 + 16, 6, cpu_c, scale=3)
        # status
        if self._winner is not None:
            msg = "YOU WIN" if self._winner == "you" else "CPU WINS"
            col = lcd.color(120, 255, 120) if self._winner == "you" else lcd.color(255, 100, 100)
            display.text_scaled(lcd, msg, self._w // 2 - 56, self._h // 2 - 12, col, scale=2)
            lcd.fb.text("SEL: retry", self._w // 2 - 36, self._h // 2 + 12, 0xFFFF)
        elif self._waiting:
            lcd.fb.text("SEL: serve  UP/DOWN: move",
                        self._w // 2 - 96, self._h // 2 + 18, 0xFFFF)

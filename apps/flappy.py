# Flappy: SELECT (or UP) flaps; gravity does the rest. BACK exits.
import random
from core.app import App
from core import input as ev
from core import display, led


BIRD_X = 60
BIRD_R = 6
GRAV = 0.6
FLAP_VY = -5.2
PIPE_W = 22
PIPE_GAP = 56
PIPE_SPEED = 3
SPAWN_FRAMES = 28


_PAGE = b"""<h1>Flappy</h1>
<section class="card" style="text-align:center"><div id="root"></div></section>
<script type="module">
import { html, render, useState, useEffect, useRef } from '/vendor/preact.js';
function Game(){
  const cvRef=useRef(null);
  const restartRef=useRef(()=>{});
  const [hud,setHud]=useState({score:0,best:0,dead:false});
  useEffect(()=>{
    const cv=cvRef.current, ctx=cv.getContext('2d');
    const W=cv.width, H=cv.height;
    let bird,pipes,lastSpawn,frame,dead,score;
    let best=parseInt(localStorage.getItem('flappy-best')||'0',10);
    function reset(){
      bird={x:60,y:H/2,vy:0}; pipes=[]; lastSpawn=0; frame=0;
      dead=false; score=0;
      setHud({score:0,best,dead:false});
    }
    function flap(){ if(dead){reset();return;} bird.vy=-5.6; }
    function die(){
      dead=true;
      if(score>best){best=score; localStorage.setItem('flappy-best',String(best));}
      setHud({score,best,dead:true});
    }
    restartRef.current=reset;
    cv.addEventListener('pointerdown',e=>{e.preventDefault();flap();});
    const onKey=e=>{ if(e.code==='Space'||e.key==='ArrowUp'||e.key==='Enter'){e.preventDefault();flap();} };
    window.addEventListener('keydown',onKey);
    let raf=0;
    function loop(){
      frame++;
      if(!dead){
        bird.vy+=0.42; bird.y+=bird.vy;
        if(frame-lastSpawn>72){
          lastSpawn=frame;
          const gy=40+Math.random()*(H-160);
          pipes.push({x:W,gy,scored:false});
        }
        pipes.forEach(p=>p.x-=2.2);
        pipes=pipes.filter(p=>p.x>-40);
        if(bird.y<8||bird.y>H-8) die();
        for(const p of pipes){
          if(p.x<bird.x+8 && p.x+30>bird.x-8){
            if(bird.y-8<p.gy || bird.y+8>p.gy+100){die();break;}
          }
          if(!p.scored && p.x+30<bird.x-8){
            p.scored=true; score++;
            setHud(s=>({...s,score}));
          }
        }
      }
      const g=ctx.createLinearGradient(0,0,0,H);
      g.addColorStop(0,'#b6dcec'); g.addColorStop(1,'#82bdd6');
      ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
      ctx.fillStyle='#4ea34e';
      pipes.forEach(p=>{ctx.fillRect(p.x,0,30,p.gy); ctx.fillRect(p.x,p.gy+100,30,H-p.gy-100);});
      ctx.fillStyle='#356f35';
      pipes.forEach(p=>{ctx.fillRect(p.x-3,p.gy-6,36,6); ctx.fillRect(p.x-3,p.gy+100,36,6);});
      ctx.fillStyle=dead?'#999':'#f4c100';
      ctx.beginPath(); ctx.arc(bird.x,bird.y,9,0,Math.PI*2); ctx.fill();
      ctx.fillStyle='#000'; ctx.fillRect(bird.x+3,bird.y-3,2,2);
      ctx.fillStyle='#df5830'; ctx.fillRect(bird.x+7,bird.y,4,2);
      raf=requestAnimationFrame(loop);
    }
    reset(); loop();
    return ()=>{cancelAnimationFrame(raf); window.removeEventListener('keydown',onKey);};
  },[]);
  return html`
    <canvas ref=${cvRef} width="360" height="420"
      style="max-width:100%;width:100%;height:auto;border-radius:.55rem;display:block;margin:0 auto;touch-action:manipulation;cursor:pointer;background:#82bdd6"/>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.7rem">
      <span class="muted">Score</span>
      <span style="font:800 1.6rem ui-monospace,monospace;color:var(--primary)">${hud.score}</span>
      <span class="muted">Best ${hud.best}</span>
    </div>
    <p class="muted" style="margin:.5rem 0 0;font-size:.82rem">Tap the canvas or press Space to flap</p>
    ${hud.dead ? html`<button class="primary" style="margin-top:.6rem;width:100%" onClick=${()=>restartRef.current()}>Play again</button>` : ''}
  `;
}
render(html`<${Game}/>`, document.getElementById('root'));
</script>"""


class Flappy(App):
    name = "flappy"
    wants_screensaver = False

    def __init__(self):
        self._w = 320
        self._h = 150
        self._reset()

    def _reset(self):
        self._bird_y = self._h / 2.0
        self._vy = 0.0
        self._pipes = []            # [x, gap_y, scored]
        self._spawn = SPAWN_FRAMES  # spawn one immediately
        self._score = 0
        self._best = getattr(self, "_best", 0)
        self._dead = False
        self._flash = 0

    def on_enter(self):
        self._w = display.width()
        self._h = display.height() - display.ip_bar_height()
        self._reset()
        led.off()

    def on_exit(self):
        led.off()

    def on_input(self, e):
        if self._dead:
            if e in (ev.SELECT, ev.NAV_UP, ev.NAV_DOWN):
                self._reset()
            return
        if e in (ev.SELECT, ev.NAV_UP):
            self._vy = FLAP_VY

    def on_tick(self, dt):
        if self._flash > 0:
            self._flash -= 1
            if self._flash <= 0:
                led.off()
        if self._dead:
            return

        self._vy += GRAV
        self._bird_y += self._vy
        if self._bird_y < BIRD_R or self._bird_y > self._h - BIRD_R:
            self._die()
            return

        self._spawn += 1
        if self._spawn >= SPAWN_FRAMES:
            self._spawn = 0
            gy = random.randint(15, self._h - 15 - PIPE_GAP)
            self._pipes.append([self._w, gy, False])

        keep = []
        for p in self._pipes:
            p[0] -= PIPE_SPEED
            if p[0] + PIPE_W > 0:
                keep.append(p)
        self._pipes = keep

        by = int(self._bird_y)
        for p in self._pipes:
            px, gy, scored = p
            if px < BIRD_X + BIRD_R and px + PIPE_W > BIRD_X - BIRD_R:
                if by - BIRD_R < gy or by + BIRD_R > gy + PIPE_GAP:
                    self._die()
                    return
            if not scored and px + PIPE_W < BIRD_X - BIRD_R:
                p[2] = True
                self._score += 1
                if self._score > self._best:
                    self._best = self._score
                led.set_color(0, 16, 0)
                self._flash = 3

    def _die(self):
        self._dead = True
        led.set_color(24, 0, 0)
        self._flash = 15

    def on_web(self, method, subpath, params, body):
        from core import web_server
        return web_server.page("flappy", _PAGE)

    def on_draw(self, lcd):
        lcd.fb.fill(lcd.color(70, 130, 180))
        pc = lcd.color(60, 180, 60)
        pe = lcd.color(40, 130, 40)
        for p in self._pipes:
            x, gy, _ = p
            x = int(x)
            lcd.fb.fill_rect(x, 0, PIPE_W, gy, pc)
            lcd.fb.fill_rect(x, gy + PIPE_GAP, PIPE_W,
                             self._h - (gy + PIPE_GAP), pc)
            lcd.fb.fill_rect(x - 2, gy - 4, PIPE_W + 4, 4, pe)
            lcd.fb.fill_rect(x - 2, gy + PIPE_GAP, PIPE_W + 4, 4, pe)

        by = int(self._bird_y)
        body = lcd.color(255, 220, 0)
        wing = lcd.color(220, 160, 0)
        lcd.fb.fill_rect(BIRD_X - BIRD_R, by - BIRD_R, BIRD_R * 2, BIRD_R * 2, body)
        lcd.fb.fill_rect(BIRD_X - BIRD_R + 1, by + 1, BIRD_R, 3, wing)
        lcd.fb.fill_rect(BIRD_X + 2, by - 3, 2, 2, 0)             # eye
        lcd.fb.fill_rect(BIRD_X + BIRD_R - 1, by, 3, 1, lcd.color(255, 80, 40))   # beak

        display.text_scaled(lcd, str(self._score), 8, 6, 0xFFFF, scale=2)
        if self._best:
            lcd.fb.text("best " + str(self._best), 8, 30, lcd.color(220, 220, 220))

        if self._dead:
            cx = self._w // 2 - 72
            cy = self._h // 2 - 16
            display.text_scaled(lcd, "GAME OVER", cx, cy,
                                lcd.color(255, 80, 80), scale=2)
            lcd.fb.text("SEL: retry  BACK: exit",
                        self._w // 2 - 80, cy + 24, 0xFFFF)

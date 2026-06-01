# Stacker: a row slides left-right; SELECT locks it. Misaligned cells fall.
# Reach the top to win. BACK exits.
from core.app import App
from core import input as ev
from core import display, led


CELL = 20
HSPACE = 2
START_LEN = 5


_PAGE = b"""<h1>Stacker</h1>
<section class="card"><div id="root"></div></section>
<script type="module">
import { html, render, useState, useEffect, useRef } from '/vendor/preact.js';
function Game(){
  const cvRef=useRef(null);
  const ctlRef=useRef({lock:()=>{},restart:()=>{}});
  const [hud,setHud]=useState({level:1,target:9,dead:false,won:false,best:0});
  useEffect(()=>{
    const cv=cvRef.current, ctx=cv.getContext('2d');
    const W=cv.width, H=cv.height;
    const COLS=10, CELL=W/COLS;
    const ROWS=Math.floor(H/CELL)-1;
    let stack,curLen,curLeft,dir,moveAcc,moveSpeed,level,dead,won;
    let best=parseInt(localStorage.getItem('stacker-best')||'0',10);
    function reset(){
      const startLen=4;
      const left=Math.floor((COLS-startLen)/2);
      stack=[{l:left,r:left+startLen-1}];
      curLen=startLen; curLeft=0; dir=1; moveAcc=0; moveSpeed=8;
      level=1; dead=false; won=false;
      setHud({level,target:ROWS,dead:false,won:false,best});
    }
    function lock(){
      if(dead||won){reset();return;}
      const prev=stack[stack.length-1];
      const cl=curLeft, cr=curLeft+curLen-1;
      const nl=Math.max(prev.l,cl), nr=Math.min(prev.r,cr);
      if(nl>nr){
        dead=true;
        setHud({level,target:ROWS,dead:true,won:false,best});
        return;
      }
      stack.push({l:nl,r:nr});
      curLen=nr-nl+1;
      if(stack.length>=ROWS+1){
        won=true;
        if(level>best){best=level; localStorage.setItem('stacker-best',String(best));}
        setHud({level,target:ROWS,dead:false,won:true,best});
        return;
      }
      curLeft=0; dir=1;
      if(moveSpeed>2 && level%2===0) moveSpeed--;
      level++;
      setHud(s=>({...s,level}));
    }
    ctlRef.current={lock,restart:reset};
    const onKey=e=>{ if(e.code==='Space'||e.key==='Enter'){e.preventDefault();lock();} };
    window.addEventListener('keydown',onKey);
    cv.addEventListener('pointerdown',e=>{e.preventDefault();lock();});
    let raf=0;
    function loop(){
      if(!dead && !won){
        moveAcc++;
        if(moveAcc>=moveSpeed){
          moveAcc=0;
          curLeft+=dir;
          if(curLeft+curLen-1>=COLS-1){curLeft=COLS-curLen; dir=-1;}
          else if(curLeft<=0){curLeft=0; dir=1;}
        }
      }
      ctx.fillStyle='#141b28'; ctx.fillRect(0,0,W,H);
      for(let i=0;i<stack.length;i++){
        const row=stack[i];
        const y=H-(i+1)*CELL;
        const t=i/ROWS;
        const r=Math.floor(60+(255-60)*t);
        const g=Math.floor(160-60*t);
        const b=Math.floor(220-180*t);
        ctx.fillStyle='rgb('+r+','+g+','+b+')';
        ctx.fillRect(row.l*CELL+1, y+1, (row.r-row.l+1)*CELL-2, CELL-2);
      }
      if(!dead && !won){
        const y=H-(stack.length+1)*CELL;
        if(y>=-CELL){
          ctx.fillStyle='#f4c100';
          ctx.fillRect(curLeft*CELL+1, y+1, curLen*CELL-2, CELL-2);
        }
      }
      raf=requestAnimationFrame(loop);
    }
    reset(); loop();
    return ()=>{cancelAnimationFrame(raf); window.removeEventListener('keydown',onKey);};
  },[]);
  return html`
    <canvas ref=${cvRef} width="320" height="400"
      style="max-width:100%;width:100%;height:auto;border-radius:.55rem;display:block;margin:0 auto;touch-action:manipulation;cursor:pointer;background:#141b28"/>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.7rem">
      <span class="muted">Level</span>
      <span style="font:800 1.6rem ui-monospace,monospace;color:var(--primary)">${hud.level}/${hud.target}</span>
      <span class="muted">Best ${hud.best}</span>
    </div>
    ${hud.won ? html`<p style="text-align:center;color:#3a8;font-weight:700;margin:.5rem 0 0">Stacked!</p>`
      : hud.dead ? html`<p style="text-align:center;color:#c43;font-weight:700;margin:.5rem 0 0">Miss!</p>` : ''}
    <button class="primary" style="margin-top:.6rem;width:100%" onClick=${()=>ctlRef.current.lock()}>
      ${hud.dead || hud.won ? 'Restart' : 'Lock row'}
    </button>
    <p class="muted" style="margin:.5rem 0 0;text-align:center;font-size:.82rem">Tap canvas or press Space</p>
  `;
}
render(html`<${Game}/>`, document.getElementById('root'));
</script>"""


class Stacker(App):
    name = "stacker"
    wants_screensaver = False

    def __init__(self):
        self._w = 320
        self._h = 150
        self._best = 0
        self._reset()

    def _reset(self):
        self._cols = max(6, self._w // CELL)
        # bottom row, centered
        base_l = (self._cols - START_LEN) // 2
        self._stack = [(base_l, base_l + START_LEN - 1)]
        self._cur_len = START_LEN
        self._cur_left = 0
        self._dir = 1
        self._move_acc = 0
        self._move_speed = 4    # frames between cell steps; lower = faster
        self._level = 1
        self._target_rows = max(5, self._h // CELL - 1)
        self._dead = False
        self._won = False
        self._flash = 0

    def on_enter(self):
        self._w = display.width()
        self._h = display.height() - display.ip_bar_height()
        self._reset()
        led.off()

    def on_exit(self):
        led.off()

    def on_input(self, e):
        if self._dead or self._won:
            if e == ev.SELECT:
                self._reset()
            return
        if e == ev.SELECT:
            self._lock()

    def _lock(self):
        prev_l, prev_r = self._stack[-1]
        cur_l = self._cur_left
        cur_r = cur_l + self._cur_len - 1
        new_l = max(prev_l, cur_l)
        new_r = min(prev_r, cur_r)
        if new_l > new_r:
            self._dead = True
            led.set_color(24, 0, 0)
            self._flash = 18
            return
        perfect = (new_l == cur_l and new_r == cur_r)
        led.set_color(0, 24, 6 if perfect else 0)
        self._flash = 6
        self._stack.append((new_l, new_r))
        self._cur_len = new_r - new_l + 1
        if len(self._stack) >= self._target_rows + 1:
            self._won = True
            if self._level > self._best:
                self._best = self._level
            led.set_color(0, 24, 12)
            self._flash = 30
            return
        self._cur_left = 0
        self._dir = 1
        if self._move_speed > 1 and self._level % 2 == 0:
            self._move_speed -= 1
        self._level += 1

    def on_tick(self, dt):
        if self._flash > 0:
            self._flash -= 1
            if self._flash <= 0:
                led.off()
        if self._dead or self._won:
            return
        self._move_acc += 1
        if self._move_acc >= self._move_speed:
            self._move_acc = 0
            self._cur_left += self._dir
            if self._cur_left + self._cur_len - 1 >= self._cols - 1:
                self._cur_left = self._cols - self._cur_len
                self._dir = -1
            elif self._cur_left <= 0:
                self._cur_left = 0
                self._dir = 1

    def on_web(self, method, subpath, params, body):
        from core import web_server
        return web_server.page("stacker", _PAGE)

    def _row_color(self, lcd, i):
        # gradient sky-blue at base to warm orange near the top
        t = min(1.0, i / float(self._target_rows))
        r = int(60 + (255 - 60) * t)
        g = int(160 - 60 * t)
        b = int(220 - 180 * t)
        return lcd.color(r, g, b)

    def on_draw(self, lcd):
        lcd.fb.fill(lcd.color(16, 22, 36))
        ox = (self._w - self._cols * CELL) // 2
        # locked stack from bottom
        for i, (l, r) in enumerate(self._stack):
            y = self._h - (i + 1) * CELL
            c = self._row_color(lcd, i)
            lcd.fb.fill_rect(ox + l * CELL + HSPACE, y + HSPACE,
                             (r - l + 1) * CELL - HSPACE * 2,
                             CELL - HSPACE * 2, c)
        # moving row
        if not (self._dead or self._won):
            y = self._h - (len(self._stack) + 1) * CELL
            if y >= 0:
                c = lcd.color(255, 220, 0)
                lcd.fb.fill_rect(ox + self._cur_left * CELL + HSPACE, y + HSPACE,
                                 self._cur_len * CELL - HSPACE * 2,
                                 CELL - HSPACE * 2, c)
        # HUD
        lcd.fb.text("lv {}/{}".format(self._level, self._target_rows),
                    8, 4, 0xFFFF)
        if self._best:
            lcd.fb.text("best " + str(self._best),
                        self._w - 70, 4, lcd.color(220, 220, 220))
        if self._won:
            display.text_scaled(lcd, "STACKED!", self._w // 2 - 64, 16,
                                lcd.color(120, 255, 160), scale=2)
            lcd.fb.text("SEL: again", self._w // 2 - 36, 40, 0xFFFF)
        elif self._dead:
            display.text_scaled(lcd, "MISS!", self._w // 2 - 36, 16,
                                lcd.color(255, 100, 100), scale=2)
            lcd.fb.text("SEL: retry", self._w // 2 - 36, 40, 0xFFFF)

# Demo: live system info (free/used RAM, CPU clock, uptime).
# SELECT runs gc.collect(). Shows reading runtime state each frame.
from core.app import App
from core import input as ev
from core import display
import gc
import machine
import time


class SysInfo(App):
    name = "sysinfo"
    wants_screensaver = False

    def __init__(self):
        self._boot = time.ticks_ms()

    def on_input(self, e):
        if e == ev.SELECT:
            gc.collect()

    def on_draw(self, lcd):
        sb = display.status_bar_height()
        lcd.fb.fill_rect(0, sb, lcd.width, lcd.height - sb, 0)

        free = gc.mem_free()
        used = gc.mem_alloc()
        try:
            mhz = machine.freq() // 1000000
        except Exception:
            mhz = 0
        up = time.ticks_diff(time.ticks_ms(), self._boot) // 1000

        dim = lcd.color(170, 170, 170)
        lines = [
            ("sysinfo", lcd.color(255, 220, 0), 2),
            ("", 0, 1),
            ("RAM free", dim, 1),
            ("%d KB" % (free // 1024), 0xFFFF, 2),
            ("RAM used", dim, 1),
            ("%d KB" % (used // 1024), 0xFFFF, 2),
            ("CPU", dim, 1),
            ("%d MHz" % mhz, 0xFFFF, 2),
            ("uptime", dim, 1),
            ("%d s" % up, 0xFFFF, 2),
        ]
        y = sb + 10
        for text, color, scale in lines:
            display.text_scaled(lcd, text, 8, y, color, scale=scale)
            y += 8 * scale + 6

        display.text_scaled(lcd, "SEL: gc.collect", 8, lcd.height - 22,
                            lcd.color(120, 120, 120), scale=1)

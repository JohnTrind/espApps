"""Passive BLE advertisement listener.

Many devices keep their local name out of the advertisement payload
(modern phones rotate MAC + drop the name for privacy), so we also
parse the manufacturer-specific data (BLE adv type 0xFF) and look up
the company ID. For Apple in particular we crack the subtype byte so
"unnamed" rows become "Apple (AirPods)", "Apple (FindMy)" and so on.

This is the foundation for the ibeacon / findmy sister apps.
"""
import time
from core.app import App
from core import display

try:
    import bluetooth
    _BT_OK = True
except ImportError:
    bluetooth = None
    _BT_OK = False

_IRQ_SCAN_RESULT = 5
_STALE_MS = 30000


# A tiny slice of the BT SIG Assigned Numbers -- enough to label the
# devices you'll typically see at home. Add as needed.
_VENDORS = {
    0x004C: "Apple",
    0x0006: "Microsoft",
    0x00E0: "Google",
    0x0075: "Samsung",
    0x0087: "Garmin",
    0x008A: "Bose",
    0x05A7: "Sonos",
    0x012D: "Sony",
    0x0157: "Huami",          # Xiaomi / Amazfit
    0x0499: "Ruuvi",
    0x0059: "Nordic Semi",
    0x000F: "Broadcom",
    0x000D: "TI",
    0x02FE: "Tile",
    0x0001: "Ericsson",
    0x008C: "Gimbal",
}

# Apple's manufacturer data layout: bytes 0-1 are the company ID
# (0x004C little-endian), byte 2 is the "type" of continuity message.
_APPLE_SUBTYPES = {
    0x02: "iBeacon",
    0x05: "AirDrop",
    0x06: "Homekit",
    0x07: "AirPods",
    0x08: "Hey Siri",
    0x09: "AirPlay",
    0x0a: "Magic Switch",
    0x0b: "Watch Connection",
    0x0c: "Handoff",
    0x0d: "Wi-Fi Settings",
    0x0e: "Instant Hotspot",
    0x0f: "Wi-Fi Join",
    0x10: "Nearby Info",
    0x11: "Apple TV",
    0x12: "FindMy",
}


_PAGE = b"""<h1>BT Scan</h1>
<section class="card">
  <div style="display:flex;align-items:center;gap:.5rem">
    <p class="muted" style="flex:1;margin:0" id="status">scanning...</p>
  </div>
  <ul class="list" id="devs" style="margin-top:.5rem"></ul>
</section>
<script>
const $=id=>document.getElementById(id);
function bars(rssi){
  const s = rssi >= -55 ? 4 : rssi >= -68 ? 3 : rssi >= -80 ? 2 : rssi >= -90 ? 1 : 0;
  let o=''; for(let i=0;i<4;i++) o += i<s ? '|' : '.';
  return o;
}
function label(d){
  if(d.name) return d.name;
  if(d.kind && d.vendor) return d.vendor+' ('+d.kind+')';
  if(d.kind) return d.kind;
  if(d.vendor) return d.vendor;
  return '(anonymous)';
}
async function tick(){
  try{
    const j=await (await fetch('/app/btscan/state')).json();
    if(!j.ok){ $('status').textContent='ble unavailable'; return; }
    const devs=j.devices||[];
    const ul=$('devs'); ul.innerHTML='';
    devs.forEach(d=>{
      const li=document.createElement('li');
      const left=document.createElement('span'); left.className='nm';
      left.textContent=label(d);
      const right=document.createElement('span'); right.className='sz';
      right.textContent=bars(d.rssi)+' '+d.rssi+'dBm  '+d.addr;
      li.appendChild(left); li.appendChild(right);
      ul.appendChild(li);
    });
    $('status').textContent=devs.length+' device'+(devs.length===1?'':'s')+' nearby';
  }catch(e){ $('status').textContent='offline'; }
}
tick();
setInterval(tick,2500);
</script>"""


def _parse_adv(adv):
    """Pull useful bits out of an advertisement payload.

    Returns dict with: name, vendor, vendor_id, kind. We deliberately
    ignore the long tail of fields; only enough to label the row."""
    out = {"name": "", "vendor": "", "vendor_id": None, "kind": ""}
    if not adv:
        return out
    i = 0
    n = len(adv)
    while i + 1 < n:
        ln = adv[i]
        if ln == 0 or i + ln >= n:
            break
        t = adv[i + 1]
        payload = adv[i + 2:i + 1 + ln]

        if t in (8, 9) and not out["name"]:
            try:
                out["name"] = bytes(payload).decode("utf-8")
            except UnicodeError:
                pass

        elif t == 0xFF and len(payload) >= 2:
            mid = payload[0] | (payload[1] << 8)        # little-endian
            out["vendor_id"] = mid
            out["vendor"] = _VENDORS.get(mid, "")
            if mid == 0x004C and len(payload) >= 3:
                sub = payload[2]
                if sub in _APPLE_SUBTYPES:
                    out["kind"] = _APPLE_SUBTYPES[sub]
            elif mid == 0x02FE:
                out["kind"] = "Tile"

        elif t == 0x16 and len(payload) >= 2:           # service data
            sid = payload[0] | (payload[1] << 8)
            if sid == 0xFEAA:
                out["kind"] = "Eddystone"
            elif sid == 0xFEED:
                out["kind"] = out["kind"] or "Tile"
            elif sid == 0xFE9F:
                out["vendor"] = out["vendor"] or "Google"
                out["kind"] = out["kind"] or "Find My Device"

        i += ln + 1
    return out


def _addr_hex(addr):
    return ":".join("{:02x}".format(b) for b in addr)


class BtScan(App):
    name = "btscan"
    wants_screensaver = False

    def __init__(self):
        self._ble = None
        self._devices = {}      # addr_hex -> dict
        self._scanning = False
        self._init_failed = False

    def on_enter(self):
        self._start_scan()

    def on_exit(self):
        self._stop_scan()

    def on_input(self, e):
        pass

    def on_tick(self, dt_ms):
        if not self._devices:
            return
        now = time.ticks_ms()
        stale = [k for k, v in self._devices.items()
                 if time.ticks_diff(now, v["last"]) > _STALE_MS]
        for k in stale:
            del self._devices[k]

    def on_draw(self, lcd):
        lcd.fb.fill(0)
        display.text_scaled(lcd, "BT scan", 8, 14, lcd.color(220, 220, 220),
                            scale=2)
        if not _BT_OK or self._init_failed:
            lcd.fb.text("BLE unavailable", 8, 50, lcd.color(220, 100, 100))
        else:
            lcd.fb.text("seen: {}".format(len(self._devices)), 8, 50,
                        lcd.color(180, 180, 100))
            top = sorted(self._devices.values(), key=lambda d: -d["rssi"])[:5]
            y = 78
            for d in top:
                label = d["name"] or d["kind"] or d["vendor"] or d["addr"]
                line = "{:>4} {}".format(d["rssi"], label[:18])
                lcd.fb.text(line, 8, y, lcd.color(220, 220, 220))
                y += 14
        lcd.fb.text("see /app/btscan/", 8, lcd.height - 40,
                    lcd.color(150, 150, 150))

    def on_web(self, method, subpath, params, body):
        if subpath == "state":
            self._start_scan()
            now = time.ticks_ms()
            devs = sorted(self._devices.values(), key=lambda d: -d["rssi"])[:30]
            return {
                "ok": _BT_OK and not self._init_failed,
                "devices": [{
                    "addr": d["addr"],
                    "rssi": d["rssi"],
                    "name": d["name"],
                    "vendor": d["vendor"],
                    "vendor_id": d["vendor_id"],
                    "kind": d["kind"],
                    "age": int(time.ticks_diff(now, d["last"]) / 1000),
                } for d in devs],
            }
        from core import web_server
        return web_server.page("bt scan", _PAGE)

    # ---- internals ----------------------------------------------------

    def _ensure_ble(self):
        if self._ble is not None or self._init_failed:
            return self._ble
        if not _BT_OK:
            self._init_failed = True
            return None
        try:
            self._ble = bluetooth.BLE()
            self._ble.active(True)
            self._ble.irq(self._irq)
            print("[btscan] BLE active")
        except Exception as e:
            print("[btscan] BLE init failed:", e)
            self._init_failed = True
            self._ble = None
        return self._ble

    def _start_scan(self):
        ble = self._ensure_ble()
        if ble is None or self._scanning:
            return
        try:
            ble.gap_scan(0, 30000, 30000, True)
            self._scanning = True
        except Exception as e:
            print("[btscan] gap_scan failed:", e)
            self._init_failed = True

    def _stop_scan(self):
        if self._ble is None or not self._scanning:
            return
        try:
            self._ble.gap_scan(None)
        except Exception:
            pass
        self._scanning = False

    def _irq(self, event, data):
        if event != _IRQ_SCAN_RESULT:
            return
        addr_type, addr, adv_type, rssi, adv_data = data
        addr_hex = _addr_hex(addr)
        prev = self._devices.get(addr_hex)
        parsed = _parse_adv(adv_data)
        # Don't lose fields we previously discovered if this packet
        # doesn't repeat them (e.g. a Scan-Response had the name).
        if prev:
            for k in ("name", "vendor", "vendor_id", "kind"):
                if not parsed[k] and prev.get(k):
                    parsed[k] = prev[k]
        self._devices[addr_hex] = {
            "addr": addr_hex,
            "rssi": rssi,
            "name": parsed["name"],
            "vendor": parsed["vendor"],
            "vendor_id": parsed["vendor_id"],
            "kind": parsed["kind"],
            "last": time.ticks_ms(),
        }

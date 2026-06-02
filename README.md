# espApps

MicroPython app launcher for the **Waveshare ESP32-S3-LCD-1.47**.

A minimal OS-like shell that runs on the device: pick an app from the LCD menu, it loads and runs. Apps are individual `.py` files dropped into `apps/` — no reflashing needed.

## Apps

| App | What it does |
|---|---|
| vicode | Web-based code editor served from SD card |
| localchat | LAN chat — anyone on the same WiFi can join |
| wifiradar | Scans nearby APs, shows SSID + RSSI on LCD |
| flappy | Flappy Bird clone on the LCD |
| pong | Pong |
| stacker | Stacker game |
| notepad | Simple text notes |
| sysinfo | CPU, memory, uptime |
| temperature | Reads temp sensor |
| focustimer | Pomodoro-style focus timer |
| taptempo | Tap BPM counter |
| touchmeter | Touch input visualizer |
| btscan | Bluetooth device scanner |
| notify | Push notification receiver |
| picker | File picker UI |
| pixelpad | Pixel drawing pad |

## Hardware

**Waveshare ESP32-S3-LCD-1.47** — ESP32-S3, ST7789 172×320 LCD, WS2812B LED, SD card slot.

## Deploy

Copy to device over USB/serial using your MicroPython tool of choice (e.g. `mpremote`, `rshell`, Thonny).

```bash
mpremote connect PORT cp -r apps/ :
mpremote connect PORT cp -r core/ :
```

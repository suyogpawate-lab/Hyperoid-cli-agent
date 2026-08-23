#!/usr/bin/env python3
import time
import json
import subprocess
import os

LOG_FILE = os.path.expanduser("~/.hyperoid_agent/sentinel.log")

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def notify(title, content):
    subprocess.Popen(f"termux-notification -t '{title}' -c '{content}' 2>/dev/null || true", shell=True)
    subprocess.Popen("termux-vibrate -d 120 2>/dev/null || true", shell=True)

last_plugged = None
last_battery_alert = False

while True:
    try:
        res = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            pct = data.get("percentage", 100)
            plugged = data.get("plugged", "UNPLUGGED")
            temp = data.get("temperature", 0.0)

            if last_plugged is not None and plugged != last_plugged:
                if plugged != "UNPLUGGED":
                    notify("HYPEROID // POWER LINK", f"External power connected. Charging at {pct}%.")
                    log(f"Power attached: {pct}%")
                else:
                    notify("HYPEROID // DISCHARGING", f"Power disconnected. Battery level: {pct}%.")
                    log(f"Power detached: {pct}%")
            last_plugged = plugged

            if pct <= 15 and not last_battery_alert and plugged == "UNPLUGGED":
                notify("HYPEROID // CRITICAL BATTERY", f"Battery depleted to {pct}%. Connect power unit.")
                subprocess.Popen("termux-tts-speak 'Warning. Battery level critical.' 2>/dev/null || true", shell=True)
                last_battery_alert = True
                log(f"Critical battery alert: {pct}%")
            elif pct > 20:
                last_battery_alert = False

            if temp >= 45.0:
                notify("HYPEROID // THERMAL ALERT", f"Core temperature high: {temp}°C.")
                log(f"Thermal threshold exceeded: {temp}°C")

    except Exception as e:
        log(f"Sentinel polling error: {e}")

    time.sleep(15)
    

#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import subprocess

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: return json.load(f)
        except Exception: pass
    return {}

cfg = load_config()
BOT_TOKEN = cfg.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = str(cfg.get("TELEGRAM_ADMIN_ID", ""))

if not BOT_TOKEN or not ADMIN_CHAT_ID:
    print("\033[1;33m[TELEGRAM_C2] Set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_ID in ~/.hyperoid_agent/config.json to activate.\033[0m")
    sys.exit(0)

print(f"\033[1;32m[TELEGRAM_C2] Bridge Online. Authenticated to Chat ID: {ADMIN_CHAT_ID}\033[0m")

def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=8)
    except Exception: pass

def process_remote_command(cmd_text):
    agent_script = os.path.expanduser("~/.hyperoid_agent/auto_agent.py")
    res = subprocess.run([sys.executable, agent_script, "--headless", cmd_text], capture_output=True, text=True, timeout=60)
    out = res.stdout.strip()
    return out if out else "Execution complete (no output)."

last_update_id = 0
while True:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
        res = requests.get(url, timeout=25)
        if res.status_code == 200:
            data = res.json()
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "").strip()

                if chat_id == ADMIN_CHAT_ID and text:
                    send_msg(f"⚡ *[HYPEROID // REMOTE C2]* Executing directive:\n`{text}`")
                    result = process_remote_command(text)
                    send_msg(f"📡 *[TELEMETRY REPORT]*:\n```\n{result[:3500]}\n```")
    except Exception:
        time.sleep(2)
              

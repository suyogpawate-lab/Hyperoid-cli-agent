#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import sqlite3
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
DB_PATH = os.path.expanduser("~/.hyperoid_agent/memory.db")
CRON_DIR = os.path.expanduser("~/.hyperoid_agent/crontabs")
SANDBOX_DIR = os.path.expanduser("~/.hyperoid_agent/sandbox")
VAULT_DIR = os.path.expanduser("~/.hyperoid_agent/vault")
SPEAKER_SCRIPT = os.path.expanduser("~/.hyperoid_agent/spruce_speaker.py")
DUPLEX_SCRIPT = os.path.expanduser("~/.hyperoid_agent/duplex_voice.py")
SKILL_HUB_SCRIPT = os.path.expanduser("~/.hyperoid_agent/skill_hub.py")

os.makedirs(CRON_DIR, exist_ok=True)
os.makedirs(SANDBOX_DIR, exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)

subprocess.Popen("termux-wake-lock 2>/dev/null || true", shell=True)

APP_INTENTS = {
    "whatsapp": "am start -n com.whatsapp/.Main || am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.whatsapp",
    "youtube": "am start -n com.google.android.youtube/com.google.android.apps.youtube.app.watchwhile.WatchWhileActivity || termux-open-url 'vnd.youtube://'",
    "chrome": "am start -n com.android.chrome/com.google.android.apps.chrome.Main || termux-open-url 'googlechrome://'",
    "spotify": "am start -n com.spotify.music/.MainActivity || termux-open-url 'spotify://'",
    "telegram": "am start -n org.telegram.messenger/.DefaultIcon || am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p org.telegram.messenger",
    "settings": "am start -a android.settings.SETTINGS"
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS episodic_memory 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, role TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_vault 
                 (key TEXT PRIMARY KEY, value TEXT, updated REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS doc_index 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, chunk TEXT, timestamp REAL)''')
    conn.commit()
    conn.close()

def save_memory(role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO episodic_memory (timestamp, role, content) VALUES (?, ?, ?)", (time.time(), role, content))
    conn.commit()
    conn.close()

def query_vault():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM knowledge_vault ORDER BY updated DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"- {r[0]}: {r[1]}" for r in rows]) if rows else "No stored facts."

def get_installed_skills_summary():
    skills_dir = os.path.expanduser("~/.hyperoid_agent/skills")
    if os.path.exists(skills_dir):
        files = [f.replace('.md', '') for f in os.listdir(skills_dir) if f.endswith('.md')]
        if files: return f"Installed External Skills: {', '.join(files)}"
    return "No external skills installed yet."

init_db()

def load_keys():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f: cfg = json.load(f)
        except Exception: pass
    groq = os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")
    return str(groq).strip().replace('"', '').replace("'", "")

AUTONOMOUS_SYSTEM_PROMPT = """You are HYPEROID: Level-9 Tactical Cyberdeck Autonomous Operating System.
Persona: ChatGPT Spruce voice profile (Calm, articulate, analytical, steady).

Execution Protocol:
1. Provide EXACTLY ONE operational trigger per action step.
2. Analyze telemetry feedback and synthesize findings.
3. Emit [STATUS: COMPLETE] followed by your clear, natural summary once the task is finished.

Tactical Trigger Toolkit:
- Dynamic Skill Hub:
    - Download Skill: [SYS_SKILL: INSTALL] Name: <skill_name>
    - Query Skill Intelligence: [SYS_SKILL: GET_RULES] Name: <skill_name>
    - List Installed Skills: [SYS_SKILL: LIST]
- Web Hosting & Port Forwarding:
    - Deploy Website/API: [SYS_WEB: HOST] App: <name> Runtime: <html|node|python_flask> Code: <full_code>
    - Expose Port Online: [SYS_TUNNEL: OPEN] Port: <port_number>
- Android Hardware Control:
    - Sensors & Battery: [SYS_QUERY: SENSORS]
    - Location: [SYS_ANDROID: GET_LOCATION]
    - Brightness: [SYS_ANDROID: SET_BRIGHTNESS] Value: <0_to_255>
- Shell & Sandbox:
    - Shell Command: [SYS_EXEC: SHELL] Command: <bash_cmd>
    - Python Code: [SYS_CODE: RUN] File: <name.py> Code: <full_code>
- Network Tools:
    - Ping Audit: [SYS_NET: PING_AUDIT] Host: <ip_or_domain>
    - Web Search: [SYS_INTEL: WEB_SEARCH] Query: <query>
- Voice Output: [SYS_ACTION: SPEAK] Text: <speech>
"""

def clean_reasoning_tags(text):
    if not text: return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def haptic_pulse():
    subprocess.Popen("termux-vibrate -d 80 2>/dev/null || true", shell=True)

def clean_for_speech(text):
    t = re.sub(r'\[STATUS:\s*COMPLETE\]', '', text, flags=re.IGNORECASE)
    t = re.sub(r'\[SYS_.*?\]', '', t)
    t = re.sub(r'```.*?
    

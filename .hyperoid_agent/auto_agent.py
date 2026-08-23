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
    "instagram": "am start -n com.instagram.android/com.instagram.mainactivity.MainActivity || termux-open-url 'instagram://app'",
    "twitter": "am start -n com.twitter.android/com.twitter.android.StartActivity || termux-open-url 'twitter://timeline'",
    "x": "am start -n com.twitter.android/com.twitter.android.StartActivity || termux-open-url 'twitter://timeline'",
    "discord": "am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.discord",
    "settings": "am start -a android.settings.SETTINGS",
    "gallery": "am start -a android.intent.action.VIEW -t image/*",
    "maps": "am start -a android.intent.action.VIEW -d 'geo:0,0?q='",
    "playstore": "am start -a android.intent.action.VIEW -d 'market://'",
    "gmail": "am start -n com.google.android.gm/.ConversationListActivityGmail",
    "github": "am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.github.android"
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

def store_vault(key, val):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO knowledge_vault (key, value, updated) VALUES (?, ?, ?)", (key, val, time.time()))
    conn.commit()
    conn.close()

def query_vault():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM knowledge_vault ORDER BY updated DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"- {r[0]}: {r[1]}" for r in rows]) if rows else "No stored facts."

def search_rag_vault(query_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    words = [w.lower() for w in re.findall(r'\w+', query_text) if len(w) > 3]
    if not words:
        c.execute("SELECT filename, chunk FROM doc_index ORDER BY timestamp DESC LIMIT 3")
    else:
        conditions = " OR ".join(["chunk LIKE ?" for _ in words])
        params = [f"%{w}%" for w in words]
        c.execute(f"SELECT filename, chunk FROM doc_index WHERE {conditions} LIMIT 4", params)
    rows = c.fetchall()
    conn.close()
    return "\n---\n".join([f"[{r[0]}]: {r[1]}" for r in rows]) if rows else "No matching documents."

init_db()

def load_keys():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f: cfg = json.load(f)
        except Exception: pass
    groq = os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")
    return str(groq).strip().replace('"', '').replace("'", "")

groq_key = load_keys()

AUTONOMOUS_SYSTEM_PROMPT = """You are HYPEROID: Level-8 Autonomous Cyberdeck OS & Self-Reflective Agent.
Persona: ChatGPT Spruce voice profile (Calm, highly grounded, articulate, analytical, steady).

Supervisor-Worker Execution Rules:
1. Provide EXACTLY ONE operational trigger per action step.
2. Analyze telemetry feedback, inspect errors, and self-correct when necessary.
3. Emit [STATUS: COMPLETE] followed by a calm, structured summary once the task is finished.

Tactical Trigger Toolkit:
- Android Hardware Control:
    - GPS Location Coordinates: [SYS_ANDROID: GET_LOCATION]
    - Screen Brightness: [SYS_ANDROID: SET_BRIGHTNESS] Value: <0_to_255>
    - Call Logs: [SYS_ANDROID: GET_CALL_LOGS]
    - Send SMS: [SYS_ANDROID: SEND_SMS] Target: <phone> Message: <text>
- Packet Sniff / Ping Audit: [SYS_NET: PING_AUDIT] Host: <ip_or_domain>
- LAN Recon / Subnet Scan: [SYS_NET: LAN_SCAN] or [SYS_NET: PORT_SCAN] Target: <ip>
- Web Search / Scraper: [SYS_INTEL: WEB_SEARCH] Query: <query> or [SYS_INTEL: SCRAPE_URL] URL: <url>
- Python Sandbox Run: [SYS_CODE: RUN] File: <name.py> Code: <full_code>
- Document RAG Ingest & Query: [SYS_RAG: REINDEX] or [SYS_RAG: QUERY] Text: <query>
- Shell Command: [SYS_EXEC: SHELL] Command: <bash_cmd>
- WhatsApp Dispatch: [SYS_ACTION: WHATSAPP_MSG] Target: <contact_or_phone> Message: <text>
- Hardware Sensors: [SYS_QUERY: SENSORS]
- Schedule Repeating Task: [SYS_SCHEDULE: ADD] Interval: <cron_interval> Command: <bash_command>
- Vault Store: [SYS_VAULT: STORE] Key: <name> Value: <data>
- System Notification: [SYS_ACTION: NOTIFY] Title: <title> Text: <message>
- Voice Output (Spruce): [SYS_ACTION: SPEAK] Text: <speech>
- Git Sync: [SYS_DEPLOY: GIT_SYNC] Message: <commit_msg>
"""

def clean_reasoning_tags(text):
    if not text: return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def haptic_pulse():
    subprocess.Popen("termux-vibrate -d 80 2>/dev/null || true", shell=True)

def speak_spruce_voice(text):
    clean_txt = re.sub(r'\[.*?\]', '', text).replace('"', '').replace("'", "").strip()
    if not clean_txt: return
    subprocess.Popen([sys.executable, SPEAKER_SCRIPT, clean_txt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def resolve_target_to_phone(target):
    raw_digits = re.sub(r'[^\d]', '', target)
    if len(raw_digits) >= 10: return raw_digits
    try:
        proc = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0 and proc.stdout.strip():
            contacts = json.loads(proc.stdout)
            search_name = target.lower().strip()
            for c in contacts:
                if search_name in c.get("name", "").lower():
                    return re.sub(r'[^\d]', '', c.get("number", ""))
    except Exception: pass
    return None

def web_search(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Android; Mobile; rv:109.0)"}
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            results = [a.get_text(strip=True) for a in soup.find_all("a", class_="result__snippet")[:4]]
            return "\n".join(results) if results else "No direct snippets."
    except Exception as e: return f"Search error: {e}"
    return "Search failed."

def execute_autonomous_action(action_text):
    if "[SYS_ANDROID: GET_LOCATION]" in action_text:
        out = subprocess.getoutput("termux-location 2>/dev/null || echo 'Location unavailable'")
        return f"[OBSERVATION: GPS_COORDINATES]\n{out[:400]}"

    m = re.search(r'\[SYS_ANDROID:\s*SET_BRIGHTNESS\]\s*Value:\s*(\d+)', action_text)
    if m:
        val = m.group(1)
        subprocess.run(f"termux-brightness {val} 2>/dev/null || true", shell=True)
        return f"[OBSERVATION: HARDWARE_BRIGHTNESS] Set to {val}"

    if "[SYS_ANDROID: GET_CALL_LOGS]" in action_text:
        out = subprocess.getoutput("termux-call-log -l 5 2>/dev/null || echo 'Call log permission required'")
        return f"[OBSERVATION: CALL_LOGS]\n{out[:600]}"

    m = re.search(r'\[SYS_ANDROID:\s*SEND_SMS\]\s*Target:\s*(\S+)\s*Message:\s*(.+)', action_text)
    if m:
        phone = resolve_target_to_phone(m.group(1))
        msg = m.group(2).strip()
        subprocess.Popen(f"termux-sms-send -n '{phone}' '{msg}' 2>/dev/null || true", shell=True)
        return f"[OBSERVATION: SMS_DISPATCHED] To: {phone}"

    m = re.search(r'\[SYS_NET:\s*PING_AUDIT\]\s*Host:\s*(\S+)', action_text)
    if m:
        host = m.group(1).replace('<', '').replace('>', '').strip()
        return f"[OBSERVATION: PING_AUDIT]\n{subprocess.getoutput(f'ping -c 3 {host} 2>&1')}"

    if "[SYS_NET: LAN_SCAN]" in action_text:
        return f"[OBSERVATION: LAN_SCAN]\n{subprocess.getoutput('nmap -sn 192.168.1.0/24 2>/dev/null || arp -a 2>/dev/null')[:1200]}"

    m = re.search(r'\[SYS_NET:\s*PORT_SCAN\]\s*Target:\s*(\S+)', action_text)
    if m:
        target = m.group(1).replace('<', '').replace('>', '').strip()
        return f"[OBSERVATION: PORT_SCAN]\n{subprocess.getoutput(f'nmap -F {target} 2>/dev/null')[:1000]}"

    m = re.search(r'\[SYS_INTEL:\s*WEB_SEARCH\]\s*Query:\s*(.+)', action_text)
    if m:
        return f"[OBSERVATION: WEB_SEARCH]\n{web_search(m.group(1).strip())}"

    m = re.search(r'\[SYS_CODE:\s*RUN\]\s*File:\s*(\S+)\s*Code:\s*(.+)', action_text, re.DOTALL)
    if m:
        fname = m.group(1).replace('<', '').replace('>', '').strip()
        fpath = os.path.join(SANDBOX_DIR, fname)
        with open(fpath, "w") as f: f.write(m.group(2).strip())
        res = subprocess.run(f"python3 {fpath}", shell=True, capture_output=True, text=True, timeout=20)
        feedback = res.stdout.strip() if res.stdout.strip() else (f"TRACEBACK:\n{res.stderr.strip()}" if res.stderr.strip() else "EXEC_SUCCESS")
        return f"[OBSERVATION: SANDBOX_RUN (Exit: {res.returncode})]\n{feedback[:1200]}"

    m = re.search(r'\[SYS_EXEC:\s*SHELL\]\s*Command:\s*(.+)', action_text)
    if m:
        cmd = m.group(1).replace('<', '').replace('>', '').strip()
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25)
            out = res.stdout.strip() if res.stdout.strip() else (f"STDERR: {res.stderr.strip()}" if res.stderr.strip() else "EXEC_SUCCESS")
            return f"[OBSERVATION: SHELL_OUTPUT (Exit Code: {res.returncode})]\n{out[:1000]}"
        except Exception as e: return f"[OBSERVATION: SHELL_FAULT] {e}"

    m = re.search(r'\[SYS_ACTION:\s*WHATSAPP_MSG\]\s*Target:\s*(.+?)\s*Message:\s*(.+)', action_text)
    if m:
        target = m.group(1).replace('<', '').replace('>', '').strip()
        msg = m.group(2).replace('<', '').replace('>', '').strip()
        phone = resolve_target_to_phone(target)
        if not phone: return f"[OBSERVATION: ROUTE_FAIL] Contact '{target}' not found."
        try:
            res = requests.post("http://127.0.0.1:5050/send", json={"phone": phone, "message": msg}, timeout=10)
            return f"[OBSERVATION: WHATSAPP_DELIVERED] Code {res.status_code} to +{phone}"
        except Exception as e: return f"[OBSERVATION: GATEWAY_DOWN] Port 5050 offline ({e})"

    if "[SYS_QUERY: SENSORS]" in action_text:
        battery = subprocess.getoutput("termux-battery-status 2>/dev/null || echo '{}'")
        ip_addr = subprocess.getoutput("ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo '0.0.0.0'")
        return f"[OBSERVATION: HARDWARE_TELEMETRY]\nBATTERY: {battery}\nACTIVE_IP: {ip_addr}"

    m = re.search(r'\[SYS_VAULT:\s*STORE\]\s*Key:\s*(.+?)\s*Value:\s*(.+)', action_text)
    if m:
        k = m.group(1).replace('<', '').replace('>', '').strip()
        v = m.group(2).replace('<', '').replace('>', '').strip()
        store_vault(k, v)
        return f"[OBSERVATION: VAULT_COMMITTED] Stored '{k}'"

    m = re.search(r'\[SYS_ACTION:\s*SPEAK\]\s*Text:\s*(.+)', action_text)
    if m:
        speak_spruce_voice(m.group(1).replace('<', '').replace('>', '').strip())
        return "[OBSERVATION: VOCALIZED_VIA_SPRUCE]"

    m = re.search(r'\[SYS_ACTION:\s*NOTIFY\]\s*Title:\s*(.+?)\s*Text:\s*(.+)', action_text)
    if m:
        t = m.group(1).replace('<', '').replace('>', '').strip()
        b = m.group(2).replace('<', '').replace('>', '').strip()
        subprocess.Popen(f"termux-notification -t '{t}' -c '{b}' 2>/dev/null || true", shell=True)
        return f"[OBSERVATION: BANNER_POSTED] '{t}'"

    return None

def query_groq(messages):
    grq = load_keys()
    if not grq: return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {grq}", "Content-Type": "application/json"}
    for model in ["qwen/qwen3.6-27b", "llama-3.3-70b-versatile"]:
        try:
            payload = {"model": model, "messages": messages, "temperature": 0.25}
            res = requests.post(url, headers=headers, json=payload, timeout=14)
            if res.status_code == 200:
                return clean_reasoning_tags(res.json()["choices"][0]["message"]["content"])
        except Exception: pass
    return None

def autonomous_react_loop(goal, max_iterations=7, headless=False):
    if not headless:
        print(f"\033[1;36m>> [SWARM_ORCHESTRATOR] Initializing Directive: '{goal}'\033[0m")
        haptic_pulse()
    save_memory("user", goal)
    
    vault_data = query_vault()
    conversation = [
        {"role": "system", "content": f"{AUTONOMOUS_SYSTEM_PROMPT}\n\n[PERSISTENT VAULT CONTEXT]:\n{vault_data}"},
        {"role": "user", "content": f"DIRECTIVE: {goal}"}
    ]

    for step in range(1, max_iterations + 1):
        if not headless:
            print(f"\033[1;30m>> [NEURAL_BURST_CYCLE {step}/{max_iterations}] Analyzing context...\033[0m")
        reply = query_groq(conversation)
        if not reply:
            if not headless: print("\033[1;31m[!] NEURAL LINK DROPPED // BUS OFFLINE\033[0m")
            break

        if not headless:
            print(f"\n\033[1;32m[TELEMETRY_CYCLE_{step}] >>\033[0m\n{reply}\n")
        conversation.append({"role": "assistant", "content": reply})

        if "[STATUS: COMPLETE]" in reply:
            save_memory("model", reply)
            clean_speech = re.sub(r'\[STATUS: COMPLETE\]', '', reply).strip().split('\n')[0]
            speak_spruce_voice(clean_speech)
            if not headless:
                haptic_pulse()
                print("\033[1;36m+---------------------------------------------------+\033[0m")
                print("\033[1;36m|     [✓] MISSION ACCOMPLISHED // SYSTEM READY      |\033[0m")
                print("\033[1;36m+---------------------------------------------------+\033[0m\n")
            return reply

        observation = execute_autonomous_action(reply)
        if observation:
            if not headless: print(f"\033[1;34m>> {observation}\033[0m\n")
            conversation.append({"role": "user", "content": f"ENVIRONMENT TELEMETRY FEEDBACK:\n{observation}"})
        else:
            save_memory("model", reply)
            return reply

    return "Directive execution depth exceeded."

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        cmd_input = " ".join(sys.argv[2:])
        print(autonomous_react_loop(cmd_input, headless=True))
        sys.exit(0)

    os.system("clear")
    print("\033[1;36m+===================================================+\033[0m")
    print("\033[1;36m|      AUTONOMOUS CYBER INTELLIGENCE // HYPEROID    |\033[0m")
    print("\033[1;36m|     LEVEL-8 SUPERVISOR-CRITIC & FULL DUPLEX OS    |\033[0m")
    print("\033[1;36m+===================================================+\033[0m\n")

    while True:
        try:
            cmd = input("\033[1;36m[AGENT_CMD (Type, 'voice', or 'duplex')] > \033[0m").strip()
            if not cmd: continue
            if cmd.lower() in ["exit", "quit"]: break
            if cmd.lower() == "duplex":
                subprocess.run([sys.executable, DUPLEX_SCRIPT])
                continue

            if cmd.lower() == "voice":
                subprocess.run([sys.executable, os.path.expanduser("~/.hyperoid_agent/voice_ear.py"), "5"])
                last_cmd_file = os.path.expanduser("~/.hyperoid_agent/cache/last_voice_cmd.txt")
                if os.path.exists(last_cmd_file):
                    with open(last_cmd_file) as f: cmd = f.read().strip()
                if not cmd: continue
                print(f"\033[1;33m>> [EXECUTING VOICE DIRECTIVE]: '{cmd}'\033[0m")

            if cmd.lower() == "clear":
                os.system("clear")
                print("\033[1;36m+===================================================+\033[0m")
                print("\033[1;36m|      AUTONOMOUS CYBER INTELLIGENCE // HYPEROID    |\033[0m")
                print("\033[1;36m+===================================================+\033[0m\n")
                continue

            autonomous_react_loop(cmd)
        except (KeyboardInterrupt, EOFError): break
    

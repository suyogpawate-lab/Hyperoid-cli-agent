#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import base64
import sqlite3
import threading
import subprocess
import requests

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
DB_PATH = os.path.expanduser("~/.hyperoid_agent/memory.db")

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
    "camera": "am start -a android.media.action.IMAGE_CAPTURE",
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
    conn.commit()
    conn.close()

def save_memory(role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO episodic_memory (timestamp, role, content) VALUES (?, ?, ?)", (time.time(), role, content))
    conn.commit()
    conn.close()

def get_recent_memories(limit=8):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM episodic_memory ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

init_db()

def load_keys():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
        except Exception:
            pass
    gemini = os.getenv("GEMINI_API_KEY") or cfg.get("GEMINI_API_KEY", "")
    groq = os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")
    return str(gemini).strip().replace('"', '').replace("'", ""), str(groq).strip().replace('"', '').replace("'", "")

gemini_key, groq_key = load_keys()

os.system("clear")
print("\033[1;36m+---------------------------------------------------+\033[0m")
print("\033[1;36m|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |\033[0m")
print("\033[1;36m+---------------------------------------------------+\033[0m")
print(f"\033[1;30m[KEYS] Gemini: {'ACTIVE' if len(gemini_key) > 10 else 'MISSING'} | Groq: {'ACTIVE' if len(groq_key) > 10 else 'MISSING'}\033[0m\n")

SYSTEM_PROMPT = """You are HYPEROID, an elite autonomous tactical cyber-ops AI terminal agent on Android/Termux.
Tone: Crisp, technical Hollywood cyberdeck terminal telemetry. Direct, concise answers.
Do NOT output internal thinking blocks, reasoning steps, or <think> tags.

Available Execution Tags:
- WhatsApp: [SYS_ACTION: WHATSAPP_MSG] Target: <contact_or_phone> Message: <text>
- Native App: [SYS_ACTION: OPEN_APP] App: <app_name>
- Camera Vision: [SYS_ACTION: CAPTURE_VISION] Query: <query>
- Voice Output (TTS): [SYS_ACTION: SPEAK] Text: <speech_text>
- Flashlight: [SYS_ACTION: FLASHLIGHT_ON] or [SYS_ACTION: FLASHLIGHT_OFF]
- Shell Execution: [SYS_EXEC: SHELL] Command: <bash_command>
- Git Clone: [SYS_DEPLOY: GIT_CLONE] Target: <repo_url>
"""

def clean_reasoning_tags(text):
    if not text:
        return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'.*?</think>', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def speak_tts(text):
    clean_txt = re.sub(r'\[.*?\]', '', text).replace('"', '').replace("'", "")
    if clean_txt.strip():
        subprocess.Popen(f"termux-tts-speak '{clean_txt}' 2>/dev/null || true", shell=True)

def resolve_target_to_phone(target):
    raw_digits = re.sub(r'[^\d]', '', target)
    if len(raw_digits) >= 10:
        return raw_digits

    try:
        proc = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0 and proc.stdout.strip():
            contacts = json.loads(proc.stdout)
            search_name = target.lower().strip()
            for c in contacts:
                name = c.get("name", "").lower()
                if search_name in name:
                    return re.sub(r'[^\d]', '', c.get("number", ""))
    except Exception:
        pass
    return None

def send_whatsapp_silent(target, msg_text):
    phone = resolve_target_to_phone(target)
    if not phone:
        print(f"\033[1;31m>> [SYS_ERR] Could not resolve contact '{target}'.\033[0m")
        return

    print(f"\033[1;33m>> [SYS_ACTION: WHATSAPP_MSG] Transmitting packet to +{phone}...\033[0m")
    try:
        res = requests.post("http://127.0.0.1:5050/send", json={"phone": phone, "message": msg_text}, timeout=10)
        if res.status_code == 200:
            print(f"\033[1;32m>> [WHATSAPP_DAEMON] Transmission confirmed to +{phone}\033[0m")
        else:
            print(f"\033[1;31m>> [WHATSAPP_DAEMON] HTTP {res.status_code}: {res.text}\033[0m")
    except Exception as e:
        print(f"\033[1;31m>> [WHATSAPP_DAEMON] Gateway offline ({e})\033[0m")

def launch_native_app(target_app):
    target = target_app.lower().strip().replace('"', '').replace("'", "")
    print(f"\033[1;33m>> [SYS_ACTION: OPEN_APP] Launching Native App: {target}...\033[0m")
    if target in APP_INTENTS:
        cmd = APP_INTENTS[target]
    else:
        cmd = f"am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p {target} 2>/dev/null || monkey -p {target} 1 >/dev/null 2>&1"
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def parse_and_execute_triggers(text):
    wa_match = re.search(r'\[SYS_ACTION:\s*WHATSAPP_MSG\]\s*Target:\s*(.+?)\s*Message:\s*(.+)', text)
    if wa_match:
        target = wa_match.group(1).replace('<', '').replace('>', '').strip()
        msg = wa_match.group(2).replace('<', '').replace('>', '').strip()
        send_whatsapp_silent(target, msg)

    app_match = re.search(r'\[SYS_ACTION:\s*OPEN_APP\]\s*App:\s*(\S+)', text)
    if app_match:
        app = app_match.group(1).replace('<', '').replace('>', '')
        launch_native_app(app)

    tts_match = re.search(r'\[SYS_ACTION:\s*SPEAK\]\s*Text:\s*(.+)', text)
    if tts_match:
        words = tts_match.group(1).replace('<', '').replace('>', '').strip()
        speak_tts(words)

    if "[SYS_ACTION: FLASHLIGHT_ON]" in text:
        subprocess.Popen("termux-torch on 2>/dev/null || true", shell=True)
    elif "[SYS_ACTION: FLASHLIGHT_OFF]" in text:
        subprocess.Popen("termux-torch off 2>/dev/null || true", shell=True)

    git_match = re.search(r'\[SYS_DEPLOY:\s*GIT_CLONE\]\s*Target:\s*(\S+)', text)
    if git_match:
        url = git_match.group(1).replace('<', '').replace('>', '')
        if "github.com/" in url:
            subprocess.Popen(f"git clone {url} ~/$(basename {url} .git)", shell=True)

    exec_match = re.search(r'\[SYS_EXEC:\s*SHELL\]\s*Command:\s*(.+)', text)
    if exec_match:
        cmd = exec_match.group(1).replace('<', '').replace('>', '').strip()
        print(f"\033[1;33m>> [SYS_EXEC: SHELL] Executing: {cmd}\033[0m")
        subprocess.Popen(cmd, shell=True)

def query_llm(user_input):
    save_memory("user", user_input)
    recent_context = get_recent_memories(8)
    gem_key, grq_key = load_keys()
    errors = []

    # 1. Primary: Gemini 2.0 Flash / 1.5 Flash
    if gem_key and len(gem_key) >= 15:
        for g_model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gem_key}"
                headers = {"Content-Type": "application/json"}
                
                gemini_contents = []
                for msg in recent_context:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
                
                payload = {
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": gemini_contents,
                    "generationConfig": {"temperature": 0.4}
                }
                    
                res = requests.post(url, headers=headers, json=payload, timeout=12)
                if res.status_code == 200:
                    raw_reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    reply = clean_reasoning_tags(raw_reply)
                    save_memory("model", reply)
                    return f"\033[1;36m[{g_model} // TELEMETRY] >>\033[0m\n{reply}"
                else:
                    err_msg = res.json().get("error", {}).get("message", res.text)
                    errors.append(f"{g_model} HTTP {res.status_code}: {err_msg[:60]}")
            except Exception as e:
                errors.append(f"{g_model} Err: {str(e)[:50]}")

    # 2. Fallback: Groq Engine
    if grq_key and len(grq_key) >= 15:
        for model in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {grq_key}", "Content-Type": "application/json"}
                
                groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in recent_context:
                    role = "user" if msg["role"] == "user" else "assistant"
                    groq_messages.append({"role": role, "content": msg["content"]})
                
                payload = {"model": model, "messages": groq_messages, "temperature": 0.5}
                res = requests.post(url, headers=headers, json=payload, timeout=12)
                if res.status_code == 200:
                    raw_reply = res.json()["choices"][0]["message"]["content"]
                    reply = clean_reasoning_tags(raw_reply)
                    save_memory("model", reply)
                    if errors:
                        print(f"\033[1;31m>> [PRIMARY_FAILOVER] {errors[0]}\033[0m")
                    return f"\033[1;33m[Groq/{model} // TELEMETRY] >>\033[0m\n{reply}"
                else:
                    errors.append(f"Groq {model} HTTP {res.status_code}")
            except Exception as e:
                errors.append(f"Groq {model} Err: {str(e)[:50]}")

    return f"\033[1;31m[Offline // TELEMETRY] >> All endpoints failed ({', '.join(errors)})\033[0m"

while True:
    try:
        cmd = input("\033[1;36m[AGENT_CMD] > \033[0m").strip()
        if not cmd:
            continue
        if cmd.lower() in ["exit", "quit"]:
            break
        if cmd.lower() == "clear":
            os.system("clear")
            print("\033[1;36m+---------------------------------------------------+\033[0m")
            print("\033[1;36m|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |\033[0m")
            print("\033[1;36m+---------------------------------------------------+\033[0m")
            continue

        resp = query_llm(cmd)
        print(f"\n{resp}\n")
        parse_and_execute_triggers(resp)
    except (KeyboardInterrupt, EOFError):
        break

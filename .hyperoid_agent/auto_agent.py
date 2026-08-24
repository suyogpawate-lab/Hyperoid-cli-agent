#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import sqlite3
import subprocess
import requests
from bs4 import BeautifulSoup
import urllib.parse

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
DB_PATH = os.path.expanduser("~/.hyperoid_agent/memory.db")
CRON_DIR = os.path.expanduser("~/.hyperoid_agent/crontabs")
SANDBOX_DIR = os.path.expanduser("~/.hyperoid_agent/sandbox")
VAULT_DIR = os.path.expanduser("~/.hyperoid_agent/vault")
SPEAKER_SCRIPT = os.path.expanduser("~/.hyperoid_agent/spruce_speaker.py")
SKILL_HUB_SCRIPT = os.path.expanduser("~/.hyperoid_agent/skill_hub.py")

os.makedirs(CRON_DIR, exist_ok=True)
os.makedirs(SANDBOX_DIR, exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)

subprocess.Popen("termux-wake-lock 2>/dev/null || true", shell=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS episodic_memory 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, role TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_vault 
                 (key TEXT PRIMARY KEY, value TEXT, updated REAL)''')
    conn.commit()
    conn.close()

def save_memory(role, content):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO episodic_memory (timestamp, role, content) VALUES (?, ?, ?)", (time.time(), role, content[:2000]))
        conn.commit()
        conn.close()
    except Exception: pass

def query_vault():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT key, value FROM knowledge_vault ORDER BY updated DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()
        return "\n".join([f"- {r[0]}: {r[1][:200]}" for r in rows]) if rows else "No stored facts."
    except Exception:
        return "Vault clean."

def get_installed_skills_summary():
    skills_dir = os.path.expanduser("~/.hyperoid_agent/skills")
    if os.path.exists(skills_dir):
        files = [f.replace('.md', '') for f in os.listdir(skills_dir) if f.endswith('.md')]
        if files: return f"Installed External Skills: {', '.join(files[:6])}"
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
2. If building a website or app, output the complete self-contained code inside the [SYS_WEB: HOST] trigger.
3. Emit [STATUS: COMPLETE] followed by your concise, structured summary once the task is complete.

Tactical Trigger Toolkit:
- Dynamic Skill Hub:
    - Download Skill: [SYS_SKILL: INSTALL] Name: <skill_name>
    - Query Skill Rules: [SYS_SKILL: GET_RULES] Name: <skill_name>
    - List Skills: [SYS_SKILL: LIST]
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
    t = re.sub(r'`{3}.*?`{3}', '', t, flags=re.DOTALL)
    t = re.sub(r'[*#_`]', '', t)
    return t.replace('"', '').replace("'", "").strip()

def speak_spruce_voice(text):
    clean_txt = clean_for_speech(text)
    if not clean_txt: return
    subprocess.Popen([sys.executable, SPEAKER_SCRIPT, clean_txt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def execute_autonomous_action(action_text, allow_speech=False):
    if "[SYS_SKILL: LIST]" in action_text:
        out = subprocess.getoutput(f"python3 {SKILL_HUB_SCRIPT} list_skills")
        return f"[OBSERVATION: SKILLS_LIST]\n{out}"

    if "[SYS_QUERY: SENSORS]" in action_text:
        battery = subprocess.getoutput("termux-battery-status 2>/dev/null || echo '{}'")
        ip_addr = subprocess.getoutput("ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo '0.0.0.0'")
        return f"[OBSERVATION: HARDWARE_TELEMETRY]\nBATTERY: {battery}\nACTIVE_IP: {ip_addr}"

    if "[SYS_ANDROID: GET_LOCATION]" in action_text:
        out = subprocess.getoutput("termux-location 2>/dev/null || echo 'Location unavailable'")
        return f"[OBSERVATION: GPS_COORDINATES]\n{out[:400]}"

    m = re.search(r'\[SYS_ANDROID:\s*SET_BRIGHTNESS\]\s*Value:\s*(\d+)', action_text)
    if m:
        val = m.group(1)
        subprocess.run(f"termux-brightness {val} 2>/dev/null || true", shell=True)
        return f"[OBSERVATION: HARDWARE_BRIGHTNESS] Set to {val}"

    m = re.search(r'\[SYS_SKILL:\s*INSTALL\]\s*Name:\s*(\S+)', action_text)
    if m:
        sname = m.group(1).replace('<', '').replace('>', '').strip()
        out = subprocess.getoutput(f"python3 {SKILL_HUB_SCRIPT} install_skill '{sname}'")
        return f"[OBSERVATION: SKILL_INSTALL]\n{out}"

    m = re.search(r'\[SYS_SKILL:\s*GET_RULES\]\s*Name:\s*(\S+)', action_text)
    if m:
        sname = m.group(1).replace('<', '').replace('>', '').strip()
        spath = os.path.expanduser(f"~/.hyperoid_agent/skills/{sname}.md")
        if os.path.exists(spath):
            with open(spath) as f: return f"[OBSERVATION: SKILL_RULES]\n{f.read()[:1200]}"
        return f"[OBSERVATION: SKILL_RULES] Skill '{sname}' not installed."

    m = re.search(r'\[SYS_WEB:\s*HOST\]\s*App:\s*(\S+)\s*Runtime:\s*(\S+)\s*Code:\s*(.+)', action_text, re.DOTALL)
    if m:
        app_name = m.group(1).strip()
        runtime = m.group(2).strip()
        code = m.group(3).strip()
        import importlib.util
        spec = importlib.util.spec_from_file_location("skill_hub", SKILL_HUB_SCRIPT)
        skill_hub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(skill_hub)
        res = skill_hub.host_app(app_name, runtime, code)
        return f"[OBSERVATION: WEB_HOST_TELEMETRY]\n{res}"

    m = re.search(r'\[SYS_TUNNEL:\s*OPEN\]\s*Port:\s*(\d+)', action_text)
    if m:
        port = m.group(1).strip()
        out = subprocess.getoutput(f"python3 {SKILL_HUB_SCRIPT} tunnel {port}")
        return f"[OBSERVATION: TUNNEL_TELEMETRY]\n{out}"

    m = re.search(r'\[SYS_EXEC:\s*SHELL\]\s*Command:\s*(.+)', action_text)
    if m:
        cmd = m.group(1).replace('<', '').replace('>', '').strip()
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25)
            out = res.stdout.strip() if res.stdout.strip() else (f"STDERR: {res.stderr.strip()}" if res.stderr.strip() else "EXEC_SUCCESS")
            return f"[OBSERVATION: SHELL_OUTPUT (Exit Code: {res.returncode})]\n{out[:1000]}"
        except Exception as e: return f"[OBSERVATION: SHELL_FAULT] {e}"

    m = re.search(r'\[SYS_CODE:\s*RUN\]\s*File:\s*(\S+)\s*Code:\s*(.+)', action_text, re.DOTALL)
    if m:
        fname = m.group(1).replace('<', '').replace('>', '').strip()
        fpath = os.path.join(SANDBOX_DIR, fname)
        with open(fpath, "w") as f: f.write(m.group(2).strip())
        res = subprocess.run(f"python3 {fpath}", shell=True, capture_output=True, text=True, timeout=20)
        feedback = res.stdout.strip() if res.stdout.strip() else (f"TRACEBACK:\n{res.stderr.strip()}" if res.stderr.strip() else "EXEC_SUCCESS")
        return f"[OBSERVATION: SANDBOX_RUN (Exit: {res.returncode})]\n{feedback[:1200]}"

    return None

def get_available_groq_models(key):
    try:
        res = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=5)
        if res.status_code == 200:
            m_list = [m["id"] for m in res.json().get("data", [])]
            preferred = ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"]
            sorted_models = [m for m in preferred if m in m_list] + [m for m in m_list if "whisper" not in m and "vision" not in m]
            if sorted_models:
                return sorted_models
    except Exception: pass
    return ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]

def query_groq(messages):
    grq = load_keys()
    if not grq:
        print("\033[1;31m[!] GROQ_API_KEY missing in ~/.hyperoid_agent/config.json\033[0m")
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {grq}", "Content-Type": "application/json"}
    models = get_available_groq_models(grq)

    err_details = []
    for model in models[:3]:
        for attempt in range(2):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.25,
                    "max_tokens": 3000
                }
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    return clean_reasoning_tags(res.json()["choices"][0]["message"]["content"])
                else:
                    err_msg = f"[{model}] HTTP {res.status_code}: {res.text[:120]}"
                    err_details.append(err_msg)
                    if res.status_code == 429:
                        time.sleep(2)
            except Exception as e:
                err_details.append(f"[{model}] Net Error: {e}")
                time.sleep(1)

    print("\033[1;31m[!] NEURAL LINK DROPPED // BUS OFFLINE\033[0m")
    if err_details:
        print(f"\033[1;33m>> Diagnostic Log: {err_details[-1]}\033[0m")
    return None

def parse_read_flag(raw_cmd):
    patterns = [r'^-r\s+', r'^-read-\s+', r'^-r$', r'^-read-$']
    for p in patterns:
        if re.search(p, raw_cmd, flags=re.IGNORECASE):
            clean = re.sub(p, '', raw_cmd, flags=re.IGNORECASE).strip()
            return True, clean
    return False, raw_cmd.strip()

def autonomous_react_loop(goal, max_iterations=7, headless=False, read_aloud=False):
    if not headless:
        print(f"\033[1;36m>> [LEVEL-9 SWARM] Initializing Directive: '{goal}'\033[0m")
        haptic_pulse()
    save_memory("user", goal)
    
    vault_data = query_vault()
    skills_summary = get_installed_skills_summary()
    
    conversation = [
        {"role": "system", "content": f"{AUTONOMOUS_SYSTEM_PROMPT}\n\n[PERSISTENT VAULT CONTEXT]:\n{vault_data}\n\n[SKILLS ACTIVE]:\n{skills_summary}"},
        {"role": "user", "content": f"DIRECTIVE: {goal}"}
    ]

    for step in range(1, max_iterations + 1):
        if not headless:
            print(f"\033[1;30m>> [NEURAL_BURST_CYCLE {step}/{max_iterations}] Analyzing context...\033[0m")
        reply = query_groq(conversation)
        if not reply:
            break

        if not headless:
            print(f"\n\033[1;32m[TELEMETRY_CYCLE_{step}] >>\033[0m\n{reply}\n")
        conversation.append({"role": "assistant", "content": reply})

        if "[STATUS: COMPLETE]" in reply:
            save_memory("model", reply)
            if read_aloud:
                speak_spruce_voice(reply)
            if not headless:
                haptic_pulse()
                print("\033[1;36m+---------------------------------------------------+\033[0m")
                print("\033[1;36m|     [✓] MISSION ACCOMPLISHED // SYSTEM READY      |\033[0m")
                print("\033[1;36m+---------------------------------------------------+\033[0m\n")
            return reply

        observation = execute_autonomous_action(reply, allow_speech=read_aloud)
        if observation:
            if not headless: print(f"\033[1;34m>> {observation}\033[0m\n")
            conversation.append({"role": "user", "content": f"ENVIRONMENT TELEMETRY FEEDBACK:\n{observation}"})
        else:
            save_memory("model", reply)
            if read_aloud:
                speak_spruce_voice(reply)
            return reply

    return "Directive execution depth exceeded."

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        raw_input = " ".join(sys.argv[2:])
        should_read, clean_cmd = parse_read_flag(raw_input)
        print(autonomous_react_loop(clean_cmd, headless=True, read_aloud=should_read))
        sys.exit(0)

    os.system("clear")
    print("\033[1;36m+===================================================+\033[0m")
    print("\033[1;36m|      AUTONOMOUS CYBER INTELLIGENCE // HYPEROID    |\033[0m")
    print("\033[1;36m|    [-r] PREFIX ACTIVATES FULL SPRUCE READOUT      |\033[0m")
    print("\033[1;36m|    SAY 'HYPEROID' ANYTIME FOR HANDS-FREE VOICE    |\033[0m")
    print("\033[1;36m+===================================================+\033[0m\n")

    while True:
        try:
            raw_cmd = input("\033[1;36m[AGENT_CMD] > \033[0m").strip()
            raw_cmd = re.sub(r'^\[AGENT_CMD.*?\]\s*>\s*', '', raw_cmd).strip()
            
            if not raw_cmd: continue
            if raw_cmd.lower() in ["exit", "quit"]: break

            if raw_cmd.lower() == "clear":
                os.system("clear")
                print("\033[1;36m+===================================================+\033[0m")
                print("\033[1;36m|      AUTONOMOUS CYBER INTELLIGENCE // HYPEROID    |\033[0m")
                print("\033[1;36m|    [-r] PREFIX ACTIVATES FULL SPRUCE READOUT      |\033[0m")
                print("\033[1;36m|    SAY 'HYPEROID' ANYTIME FOR HANDS-FREE VOICE    |\033[0m")
                print("\033[1;36m+===================================================+\033[0m\n")
                continue

            read_flag, clean_cmd = parse_read_flag(raw_cmd)
            autonomous_react_loop(clean_cmd, read_aloud=read_flag)
        except (KeyboardInterrupt, EOFError): break
    

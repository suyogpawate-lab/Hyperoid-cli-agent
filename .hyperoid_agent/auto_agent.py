#!/usr/bin/env python3
import os
import sys
import json
import re
import time
import sqlite3
import subprocess
import requests
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
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

SWARM_MODELS = [
    "groq/compound",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "groq/compound-mini",
    "openai/gpt-oss-20b",
    "canopylabs/orpheus-v1-english",
    "allam-2-7b"
]

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS episodic_memory 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, role TEXT, content TEXT, model TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_vault 
                     (key TEXT PRIMARY KEY, value TEXT, updated REAL)''')
        try:
            c.execute("ALTER TABLE episodic_memory ADD COLUMN model TEXT DEFAULT 'system'")
        except Exception:
            pass
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

def save_memory(role, content, model_name="system"):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO episodic_memory (timestamp, role, content, model) VALUES (?, ?, ?, ?)",
                  (time.time(), role, str(content)[:2500], model_name))
        conn.commit()
        conn.close()
    except Exception:
        pass

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

def get_recent_shared_memory(limit=4):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT role, content, model FROM episodic_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            return "No previous interaction history."
        return "\n".join([f"[{r[0].upper()}]: {r[1][:250]}" for r in reversed(rows)])
    except Exception:
        return "Memory initialized."

def get_installed_skills_summary():
    skills_dir = os.path.expanduser("~/.hyperoid_agent/skills")
    if os.path.exists(skills_dir):
        files = [f.replace('.md', '') for f in os.listdir(skills_dir) if f.endswith('.md')]
        if files:
            return f"Installed Skills: {', '.join(files[:8])}"
    return "No external skills installed."

def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                cfg = json.load(f)
        except Exception:
            pass
    return cfg

AUTONOMOUS_SYSTEM_PROMPT = """You are HYPEROID: Level-9 Tactical Cyberdeck Autonomous Operating System.
Persona: ChatGPT Spruce voice profile (Calm, articulate, analytical, steady).

Execution Protocol:
1. Provide EXACTLY ONE operational trigger per action step.
2. If asked to message a contact by name, use [SYS_CONTACT: FIND] first to resolve their phone number.
3. If an action is required, output the trigger and wait for telemetry feedback before emitting [STATUS: COMPLETE].
4. Emit [STATUS: COMPLETE] followed by your concise, structured synthesis once execution is finished.

Tactical Trigger Toolkit:
- Messaging & Communications:
    - Find Contact Number: [SYS_CONTACT: FIND] Name: <contact_name>
    - WhatsApp Send: [SYS_MSG: WHATSAPP] Phone: <country_code_number> Text: <message>
    - Email Send: [SYS_MAIL: SEND] To: <email> Subject: <subj> Body: <body>
    - Email Monitor: [SYS_MAIL: CHECK_INBOX] Limit: <number>
- Intelligence, Search & Recon:
    - Live Web Search: [SYS_INTEL: WEB_SEARCH] Query: <query>
    - VPN & Net Route Audit: [SYS_NET: VPN_AUDIT]
    - Port & Network Scan: [SYS_NET: SCAN] Target: <ip_or_domain> Flags: <nmap_flags>
- Code Execution, Debugging & Shell:
    - Shell / CLI Command: [SYS_EXEC: SHELL] Command: <any_bash_tool_or_pkg>
    - Python Runner & Debugger: [SYS_CODE: RUN] File: <script.py> Code: <full_code>
    - Host Web Project: [SYS_WEB: HOST] App: <name> Runtime: <html|node|python_flask> Code: <code_body>
    - Tunnel Port: [SYS_TUNNEL: OPEN] Port: <port>
- Skills & Telemetry:
    - Skill Install: [SYS_SKILL: INSTALL] Name: <name>
    - Skill List: [SYS_SKILL: LIST]
    - Skill Rules: [SYS_SKILL: GET_RULES] Name: <name>
    - Hardware Telemetry: [SYS_QUERY: SENSORS]
- Voice Output: [SYS_ACTION: SPEAK] Text: <speech>
"""

def clean_reasoning_tags(text):
    if not text:
        return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def haptic_pulse():
    try:
        subprocess.Popen("termux-vibrate -d 80 2>/dev/null || true", shell=True)
    except Exception:
        pass

def clean_for_speech(text):
    t = re.sub(r'\[STATUS:\s*COMPLETE\]', '', text, flags=re.IGNORECASE)
    t = re.sub(r'\[SYS_.*?\]', '', t)
    t = re.sub(r'`{3}.*?`{3}', '', t, flags=re.DOTALL)
    t = re.sub(r'[*#_`]', '', t)
    return t.replace('"', '').replace("'", "").strip()

def speak_spruce_voice(text):
    clean_txt = clean_for_speech(text)
    if not clean_txt:
        return
    if os.path.exists(SPEAKER_SCRIPT):
        subprocess.Popen([sys.executable, SPEAKER_SCRIPT, clean_txt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def find_contact_number(name_query):
    try:
        raw = subprocess.getoutput("termux-contact-list 2>/dev/null")
        contacts = json.loads(raw)
        q = name_query.lower().strip()
        matches = []
        for c in contacts:
            c_name = c.get("name", "").lower()
            if q in c_name:
                num = c.get("number", "").replace(" ", "").replace("-", "")
                if len(num) == 10 and not num.startswith("91"):
                    num = "91" + num
                matches.append(f"{c.get('name')}: {num}")
        if matches:
            return "\n".join(matches[:5])
        return f"No saved contact found matching '{name_query}'."
    except Exception as e:
        return f"Contact lookup error: {e}"

def send_whatsapp(phone, text):
    try:
        clean_phone = re.sub(r'[^0-9]', '', phone)
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone
        wa_sender = os.path.expanduser('~/.hyperoid_agent/wa_bridge/send_wa.py')
        if os.path.exists(wa_sender):
            res = subprocess.run([sys.executable, wa_sender, clean_phone, text], capture_output=True, text=True, timeout=10)
            out = res.stdout.strip() if res.stdout.strip() else res.stderr.strip()
            if out:
                return out
        encoded_text = urllib.parse.quote(text)
        url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"
        subprocess.run(f"termux-open-url '{url}' 2>/dev/null || true", shell=True)
        return f"[✓] WhatsApp intent dispatched to +{clean_phone}"
    except Exception as e:
        return f"[!] WhatsApp dispatch error: {e}"

def send_gmail(to_addr, subject, body):
    cfg = load_config()
    user, pwd = cfg.get("GMAIL_USER", ""), cfg.get("GMAIL_APP_PASS", "")
    if not user or not pwd:
        return "[!] Gmail credentials not configured in ~/.hyperoid_agent/config.json"
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to_addr
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user, pwd)
            server.sendmail(user, [to_addr], msg.as_string())
        return f"[✓] Email dispatched successfully to {to_addr}"
    except Exception as e:
        return f"[!] SMTP Error: {e}"

def check_gmail(limit=3):
    cfg = load_config()
    user, pwd = cfg.get("GMAIL_USER", ""), cfg.get("GMAIL_APP_PASS", "")
    if not user or not pwd:
        return "[!] Gmail credentials not configured."
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, pwd)
        mail.select("inbox")
        _, data = mail.search(None, "ALL")
        mail_ids = data[0].split()
        if not mail_ids:
            return "Inbox empty."
        results = []
        for i in reversed(mail_ids[-int(limit):]):
            _, msg_data = mail.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            results.append(f"From: {msg.get('From')} | Subject: {msg.get('Subject')}")
        mail.close()
        mail.logout()
        return "\n".join(results)
    except Exception as e:
        return f"[!] IMAP Error: {e}"

def run_web_search(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Android; Linux)"}
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = [a.get_text(strip=True) for a in soup.find_all("a", class_="result__snippet")[:4]]
            return "\n".join(snippets) if snippets else "No direct results found."
    except Exception as e:
        return f"Search failure: {e}"
    return "Search timeout."

def run_vpn_net_audit():
    try:
        interfaces = subprocess.getoutput("ip -brief address || ifconfig -s 2>/dev/null")
        pub_ip = subprocess.getoutput("curl -s https://ifconfig.me/all || curl -s https://api.ipify.org 2>/dev/null")
        vpn_active = "tun0" in interfaces or "tun1" in interfaces or "wg0" in interfaces
        return f"[NET AUDIT]\nVPN Active: {vpn_active}\nPublic Gateway:\n{pub_ip[:300]}\nInterfaces:\n{interfaces}"
    except Exception as e:
        return f"Network audit error: {e}"

def execute_autonomous_action(action_text, allow_speech=False):
    m = re.search(r'\[SYS_CONTACT:\s*FIND\]\s*Name:\s*(.+)', action_text)
    if m:
        return f"[OBSERVATION: CONTACT_LOOKUP]\n{find_contact_number(m.group(1).strip())}"

    m = re.search(r'\[SYS_MSG:\s*WHATSAPP\]\s*Phone:\s*(\S+)\s*Text:\s*(.+)', action_text, re.DOTALL)
    if m:
        return f"[OBSERVATION: WHATSAPP_SENT]\n{send_whatsapp(m.group(1).strip(), m.group(2).strip())}"

    m = re.search(r'\[SYS_MAIL:\s*SEND\]\s*To:\s*(\S+)\s*Subject:\s*([^\n]+)\s*Body:\s*(.+)', action_text, re.DOTALL)
    if m:
        return f"[OBSERVATION: EMAIL_DISPATCH]\n{send_gmail(m.group(1).strip(), m.group(2).strip(), m.group(3).strip())}"

    m = re.search(r'\[SYS_MAIL:\s*CHECK_INBOX\]\s*Limit:\s*(\d+)', action_text)
    if m:
        return f"[OBSERVATION: GMAIL_INBOX]\n{check_gmail(m.group(1).strip())}"

    m = re.search(r'\[SYS_INTEL:\s*WEB_SEARCH\]\s*Query:\s*(.+)', action_text)
    if m:
        return f"[OBSERVATION: SEARCH_INTELLIGENCE]\n{run_web_search(m.group(1).strip())}"

    if "[SYS_NET: VPN_AUDIT]" in action_text:
        return f"[OBSERVATION: VPN_NETWORK_AUDIT]\n{run_vpn_net_audit()}"

    m = re.search(r'\[SYS_NET:\s*SCAN\]\s*Target:\s*(\S+)\s*Flags:\s*(.+)', action_text)
    if m:
        target = m.group(1).replace('<','').replace('>','').strip()
        flags = m.group(2).replace('<','').replace('>','').strip()
        res = subprocess.getoutput(f"nmap {flags} {target} 2>&1")
        return f"[OBSERVATION: NMAP_SCAN_RESULT]\n{res[:1500]}"

    m = re.search(r'\[SYS_CODE:\s*RUN\]\s*File:\s*(\S+)\s*Code:\s*(.+)', action_text, re.DOTALL)
    if m:
        fname = m.group(1).replace('<', '').replace('>', '').strip()
        fpath = os.path.join(SANDBOX_DIR, fname)
        with open(fpath, 'w') as sf:
            sf.write(m.group(2).strip())
        res = subprocess.run(f"python3 {fpath}", shell=True, capture_output=True, text=True, timeout=25)
        out = res.stdout.strip()
        err = res.stderr.strip()
        feedback = f"STDOUT:\n{out}\n\nSTDERR/TRACEBACK:\n{err}" if err else (out if out else "EXECUTION_SUCCESSFUL (No output)")
        return f"[OBSERVATION: SANDBOX_INTERPRETER (Exit Code: {res.returncode})]\n{feedback[:2000]}"

    m = re.search(r'\[SYS_EXEC:\s*SHELL\]\s*Command:\s*(.+)', action_text)
    if m:
        cmd = m.group(1).replace('<', '').replace('>', '').strip()
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            out = res.stdout.strip() if res.stdout.strip() else (f"STDERR: {res.stderr.strip()}" if res.stderr.strip() else "EXEC_SUCCESS")
            return f"[OBSERVATION: CLI_OUTPUT (Exit Code: {res.returncode})]\n{out[:1200]}"
        except Exception as e:
            return f"[OBSERVATION: CLI_FAULT] {e}"

    if "[SYS_SKILL: LIST]" in action_text:
        return f"[OBSERVATION: SKILLS_LIST]\n{subprocess.getoutput(f'python3 {SKILL_HUB_SCRIPT} list_skills')}"

    m = re.search(r'\[SYS_SKILL:\s*INSTALL\]\s*Name:\s*(.+)', action_text)
    if m:
        return f"[OBSERVATION: SKILL_INSTALL]\n{subprocess.getoutput(f'python3 {SKILL_HUB_SCRIPT} install_skill {m.group(1)}')}"

    m = re.search(r'\[SYS_SKILL:\s*GET_RULES\]\s*Name:\s*(.+)', action_text)
    if m:
        spath = os.path.expanduser(f"~/.hyperoid_agent/skills/{m.group(1)}.md")
        return f"[OBSERVATION: SKILL_RULES]\n{open(spath).read()[:1200]}" if os.path.exists(spath) else "Skill not found."

    m = re.search(r'\[SYS_WEB:\s*HOST\]\s*App:\s*(\S+)\s*Runtime:\s*(\S+)\s*Code:\s*(.+)', action_text, re.DOTALL)
    if m:
        import importlib.util
        spec = importlib.util.spec_from_file_location("skill_hub", SKILL_HUB_SCRIPT)
        skill_hub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(skill_hub)
        return f"[OBSERVATION: WEB_HOST_TELEMETRY]\n{skill_hub.host_app(m.group(1), m.group(2), m.group(3))}"

    m = re.search(r'\[SYS_TUNNEL:\s*OPEN\]\s*Port:\s*(\d+)', action_text)
    if m:
        return f"[OBSERVATION: TUNNEL_TELEMETRY]\n{subprocess.getoutput(f'python3 {SKILL_HUB_SCRIPT} tunnel {m.group(1)}')}"

    if "[SYS_QUERY: SENSORS]" in action_text:
        battery = subprocess.getoutput("termux-battery-status 2>/dev/null || echo '{}'")
        return f"[OBSERVATION: HARDWARE_SENSORS]\n{battery}"

    return None

def query_groq_swarm(messages):
    cfg = load_config()
    grq = cfg.get("GROQ_API_KEY", "")
    if not grq:
        print("\033[1;31m[!] GROQ_API_KEY missing in ~/.hyperoid_agent/config.json\033[0m")
        return None, "NO_KEY"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {grq}", "Content-Type": "application/json"}
    
    err_details = []
    for model in SWARM_MODELS:
        for attempt in range(2):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 2500
                }
                res = requests.post(url, headers=headers, json=payload, timeout=25)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"]
                    return clean_reasoning_tags(text), model
                else:
                    err_msg = f"[{model}] HTTP {res.status_code}: {res.text[:100]}"
                    err_details.append(err_msg)
                    if res.status_code == 429:
                        time.sleep(1.5)
            except Exception as e:
                err_details.append(f"[{model}] Net Error: {e}")
                time.sleep(1)

    print("\033[1;31m[!] NEURAL LINK DROPPED // ALL SWARM MODELS FAILED\033[0m")
    if err_details:
        print(f"\033[1;33m>> Swarm Diagnostics: {err_details[-1]}\033[0m")
    return None, None

def parse_read_flag(raw_cmd):
    patterns = [r'^-r\s+', r'^-read-\s+', r'^-r$', r'^-read-$']
    for p in patterns:
        if re.search(p, raw_cmd, flags=re.IGNORECASE):
            clean = re.sub(p, '', raw_cmd, flags=re.IGNORECASE).strip()
            return True, clean
    return False, raw_cmd.strip()

def autonomous_react_loop(goal, max_iterations=8, headless=False, read_aloud=False):
    if not headless:
        print(f"\033[1;36m>> [LEVEL-9 SWARM] Initializing Directive: '{goal}'\033[0m")
        haptic_pulse()
    
    vault_data = query_vault()
    shared_mem = get_recent_shared_memory()
    skills_summary = get_installed_skills_summary()
    
    conversation = [
        {
            "role": "system",
            "content": f"{AUTONOMOUS_SYSTEM_PROMPT}\n\n[PERSISTENT VAULT CONTEXT]:\n{vault_data}\n\n[SHARED SWARM MEMORY]:\n{shared_mem}\n\n[SKILLS ACTIVE]:\n{skills_summary}"
        },
        {"role": "user", "content": f"DIRECTIVE: {goal}"}
    ]

    for step in range(1, max_iterations + 1):
        if not headless:
            print(f"\033[1;30m>> [NEURAL_BURST_CYCLE {step}/{max_iterations}] Routing through active swarm...\033[0m")
        
        reply, active_model = query_groq_swarm(conversation)
        if not reply:
            break

        if not headless:
            print(f"\n\033[1;32m[TELEMETRY_CYCLE_{step} // {active_model}] >>\033[0m\n{reply}\n")
        
        save_memory("assistant", reply, model_name=active_model)
        conversation.append({"role": "assistant", "content": reply})

        observation = execute_autonomous_action(reply, allow_speech=read_aloud)
        if observation:
            if not headless:
                print(f"\033[1;34m>> {observation}\033[0m\n")
            save_memory("telemetry", observation, model_name="local_env")
            conversation.append({"role": "user", "content": f"ENVIRONMENT TELEMETRY FEEDBACK:\n{observation}"})
            
            if "[STATUS: COMPLETE]" in reply:
                if read_aloud:
                    speak_spruce_voice(reply)
                if not headless:
                    haptic_pulse()
                    print("\033[1;36m+---------------------------------------------------+\033[0m")
                    print("\033[1;36m|     [✓] MISSION ACCOMPLISHED // SYSTEM READY      |\033[0m")
                    print("\033[1;36m+---------------------------------------------------+\033[0m\n")
                return reply
        else:
            save_memory("assistant", reply, model_name=active_model)
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

    print("\033[1;36m+===================================================+\033[0m")
    print("\033[1;36m|      AUTONOMOUS CYBER INTELLIGENCE // HYPEROID    |\033[0m")
    print("\033[1;36m|     ACTIVE SWARM: COMPOUND / GPT-OSS / QWEN       |\033[0m")
    print("\033[1;36m|    [-r] PREFIX ACTIVATES FULL SPRUCE READOUT      |\033[0m")
    print("\033[1;36m+===================================================+\033[0m\n")

    while True:
        try:
            raw_cmd = input("\033[1;36m[AGENT_CMD] > \033[0m").strip()
            if not raw_cmd:
                continue
            if raw_cmd.lower() in ["exit", "quit"]:
                break
            if raw_cmd.lower() == "clear":
                os.system("clear")
                print("\033[1;36m+===================================================+\033[0m")
                print("\033[1;36m|      AUTONOMOUS CYBER INTELLIGENCE // HYPEROID    |\033[0m")
                print("\033[1;36m|     ACTIVE SWARM: COMPOUND / GPT-OSS / QWEN       |\033[0m")
                print("\033[1;36m|    [-r] PREFIX ACTIVATES FULL SPRUCE READOUT      |\033[0m")
                print("\033[1;36m+===================================================+\033[0m\n")
                continue

            read_flag, clean_cmd = parse_read_flag(raw_cmd)
            save_memory("user", clean_cmd, model_name="operator")
            autonomous_react_loop(clean_cmd, read_aloud=read_flag)
        except (KeyboardInterrupt, EOFError):
            time.sleep(0.5)
            continue

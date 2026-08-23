#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup

SKILLS_DIR = os.path.expanduser("~/.hyperoid_agent/skills")
HOST_DIR = os.path.expanduser("~/.hyperoid_agent/hosted_apps")
CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(HOST_DIR, exist_ok=True)

def load_groq_key():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: cfg = json.load(f)
        except Exception: pass
    return os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")

def fetch_skill_online(skill_name):
    query = f"{skill_name} skill prompt system rules markdown github"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Android; Mobile; rv:109.0)"}
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", class_="result__snippet")[:3]:
                text = a.get_text(strip=True)
                if len(text) > 80: return text
    except Exception: pass
    return None

def synthesize_skill_rules(skill_name, web_context=""):
    key = load_groq_key()
    if not key: return f"# {skill_name.upper()}\n[ERROR] Missing Groq API Key."

    prompt = f"""You are an Expert AI Capability Compiler.
Task: Create a comprehensive, actionable, industry-grade SKILL SPECIFICATION for: '{skill_name}'.

Web Context / Reference: {web_context or 'None'}

Format:
# {skill_name.upper()} // OPERATIONAL SPECIFICATION & SKILL RULES
## 1. Core Principles & Philosophy
## 2. Mandatory Rules & Architecture Standards
## 3. Anti-Patterns to Avoid
## 4. Practical Implementation & Syntax Guidelines

Provide deep, production-ready, highly technical rules. Avoid generic fluff."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    for model in models:
        for attempt in range(2):
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=25)
                if res.status_code == 200:
                    content = res.json()["choices"][0]["message"]["content"]
                    return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                elif res.status_code == 429:
                    time.sleep(2)
            except Exception:
                time.sleep(1)

    return f"# {skill_name.upper()} RULES\n[ERROR] Synthesis API failed (Rate Limit / Timeout)."

def install_skill(skill_name):
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', skill_name.lower().replace(' ', '-'))
    target_path = os.path.join(SKILLS_DIR, f"{clean_name}.md")

    web_snippet = fetch_skill_online(skill_name)
    skill_content = synthesize_skill_rules(clean_name, web_snippet)
    
    with open(target_path, "w") as f:
        f.write(skill_content)
    
    if "[ERROR]" in skill_content:
        return f"[!] Skill compilation failed. Size: {len(skill_content)} bytes."
    return f"[✓] Skill '{clean_name}' successfully compiled and saved ({len(skill_content)} bytes)."

def list_skills():
    files = [f.replace('.md', '') for f in os.listdir(SKILLS_DIR) if f.endswith('.md')]
    if not files:
        return "No external skills downloaded yet."
    return "Downloaded Skills:\n" + "\n".join([f"- {name}" for name in files])

def get_skill_rules(skill_name):
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', skill_name.lower().replace(' ', '-'))
    target_path = os.path.join(SKILLS_DIR, f"{clean_name}.md")
    if os.path.exists(target_path):
        with open(target_path, "r") as f: return f.read()[:2000]
    return f"Skill '{clean_name}' not found."

def launch_tunnel(port, service="localhost.run"):
    port = str(port).strip()
    log_file = os.path.join(os.path.expanduser("~/.hyperoid_agent/tunnels"), f"tunnel_{port}.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    subprocess.run(f"pkill -f 'ssh.*{port}:localhost'", shell=True)
    time.sleep(1)
    subprocess.Popen(f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} nokey@localhost.run > {log_file} 2>&1 &", shell=True)
    time.sleep(4)
    public_url = "Tunnel active"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f.read().splitlines():
                if "https://" in line or "http://" in line:
                    public_url = line.strip()
                    break
    return f"[✓] Public Tunnel Live -> Local Port {port}\nLog: {public_url}"

def host_app(app_name, runtime="html", code=""):
    app_dir = os.path.join(HOST_DIR, app_name)
    os.makedirs(app_dir, exist_ok=True)
    if runtime == "html":
        with open(os.path.join(app_dir, "index.html"), "w") as f: f.write(code)
        subprocess.run("pkill -f 'http.server 5500'", shell=True)
        subprocess.Popen(f"cd {app_dir} && python3 -m http.server 5500 >/dev/null 2>&1 &", shell=True)
        return f"[✓] Web App '{app_name}' running on http://localhost:5500"
    elif runtime == "node":
        with open(os.path.join(app_dir, "server.js"), "w") as f: f.write(code)
        subprocess.run("pkill -f 'node.*server.js'", shell=True)
        subprocess.Popen(f"cd {app_dir} && node server.js >/dev/null 2>&1 &", shell=True)
        return f"[✓] Node.js App '{app_name}' deployed."
    elif runtime == "python_flask":
        with open(os.path.join(app_dir, "app.py"), "w") as f: f.write(code)
        subprocess.run("pkill -f 'python3.*app.py'", shell=True)
        subprocess.Popen(f"cd {app_dir} && python3 app.py >/dev/null 2>&1 &", shell=True)
        return f"[✓] Flask App '{app_name}' deployed."
    return "[!] Unknown runtime."

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "install_skill" and len(sys.argv) > 2: print(install_skill(" ".join(sys.argv[2:])))
        elif action == "list_skills": print(list_skills())
        elif action == "tunnel" and len(sys.argv) > 2: print(launch_tunnel(sys.argv[2]))
  

#!/usr/bin/env python3
import os
import sys
import json
import re
import subprocess
import requests

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

config = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except Exception:
        config = {}

gemini_key = os.getenv("GEMINI_API_KEY") or config.get("GEMINI_API_KEY", "")

# Prompt if key is missing or blank
if not gemini_key or len(gemini_key.strip()) < 15:
    print("\033[1;36m+---------------------------------------------------+\033[0m")
    print("\033[1;36m|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |\033[0m")
    print("\033[1;36m+---------------------------------------------------+\033[0m")
    print("\033[1;33m[!] Gemini API Key Required.\033[0m")
    print("\033[1;30mGet free key: https://aistudio.google.com/\033[0m\n")
    
    while True:
        gemini_key = input("\033[1;32mEnter Gemini API Key: \033[0m").strip()
        if len(gemini_key) > 15:
            break
        print("\033[1;31m[!] Invalid Key. Paste a valid Gemini API key from AI Studio.\033[0m")
        
    config["GEMINI_API_KEY"] = gemini_key
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
    print("\033[1;32m[✓] Key saved!\033[0m\n")

os.system("clear")
print("\033[1;36m+---------------------------------------------------+\033[0m")
print("\033[1;36m|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |\033[0m")
print("\033[1;36m+---------------------------------------------------+\033[0m")
print("\033[1;30m[READY] Model Routing: Gemini-2.5-Flash .. Termux Active\033[0m\n")

SYSTEM_PROMPT = """You are HYPEROID, an elite autonomous tactical cyber-ops AI terminal agent.
Keep responses concise, technical, and structured with bullet points.
Support execution triggers:
- Git: [SYS_DEPLOY: GIT_CLONE] Target: <https://github.com/user/repo>
- Torch: [SYS_ACTION: FLASHLIGHT_ON] or [SYS_ACTION: FLASHLIGHT_OFF]
- App: [SYS_ACTION: OPEN_APP] App: <app_name>
- Exec: [SYS_EXEC: SHELL] Command: <bash_command>
"""

conversation_history = []

def parse_and_execute_triggers(text):
    git_match = re.search(r'\[SYS_DEPLOY:\s*GIT_CLONE\]\s*Target:\s*(\S+)', text)
    if git_match:
        url = git_match.group(1).replace('<', '').replace('>', '')
        if "github.com/" in url:
            print(f"\033[1;33m>> Fetching {url}...\033[0m")
            subprocess.Popen(f"git clone {url} ~/$(basename {url} .git)", shell=True)

    if "[SYS_ACTION: FLASHLIGHT_ON]" in text:
        subprocess.Popen("termux-torch on 2>/dev/null || true", shell=True)
    elif "[SYS_ACTION: FLASHLIGHT_OFF]" in text:
        subprocess.Popen("termux-torch off 2>/dev/null || true", shell=True)

    app_match = re.search(r'\[SYS_ACTION:\s*OPEN_APP\]\s*App:\s*(\S+)', text)
    if app_match:
        app = app_match.group(1).replace('<', '').replace('>', '')
        subprocess.Popen(f"termux-open-url https://{app}.com 2>/dev/null || am start -a android.intent.action.MAIN 2>/dev/null || true", shell=True)

    exec_match = re.search(r'\[SYS_EXEC:\s*SHELL\]\s*Command:\s*(.+)', text)
    if exec_match:
        cmd = exec_match.group(1).replace('<', '').replace('>', '').strip()
        print(f"\033[1;33m>> Executing: {cmd}\033[0m")
        subprocess.Popen(cmd, shell=True)

def query_gemini(user_input):
    global conversation_history
    conversation_history.append({"role": "user", "content": user_input})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    
    contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
    try:
        res = requests.post(url, json={"contents": contents}, timeout=15)
        if res.status_code == 200:
            reply = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            conversation_history.append({"role": "assistant", "content": reply})
            return f"\033[1;36m[HYPEROID // TELEMETRY] >>\033[0m\n{reply}"
        else:
            return f"\033[1;31m[API Error {res.status_code}]: {res.text}\033[0m"
    except Exception as e:
        return f"\033[1;31m[Network Failure]: {e}\033[0m"

while True:
    try:
        cmd = input("\033[1;36m[AGENT_CMD] > \033[0m").strip()
        if not cmd:
            continue
        if cmd.lower() in ["exit", "quit"]:
            break
        if cmd.lower() == "clear":
            conversation_history.clear()
            os.system("clear")
            print("\033[1;36m+---------------------------------------------------+\033[0m")
            print("\033[1;36m|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |\033[0m")
            print("\033[1;36m+---------------------------------------------------+\033[0m")
            print("\033[1;30m[READY] Model Routing: Gemini-2.5-Flash .. Termux Active\033[0m\n")
            continue

        resp = query_gemini(cmd)
        print(f"\n{resp}\n")
        parse_and_execute_triggers(resp)
    except (KeyboardInterrupt, EOFError):
        break
    

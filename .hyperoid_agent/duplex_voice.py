#!/usr/bin/env python3
import os
import sys
import time
import requests
import subprocess

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
CACHE_DIR = os.path.expanduser("~/.hyperoid_agent/cache")
RAW_AUDIO = os.path.join(CACHE_DIR, "input.m4a")
os.makedirs(CACHE_DIR, exist_ok=True)

def load_groq_key():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: cfg = json.load(f)
        except Exception: pass
    return os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")

def record_and_transcribe(duration=4):
    key = load_groq_key()
    if os.path.exists(RAW_AUDIO):
        try: os.remove(RAW_AUDIO)
        except Exception: pass

    print(f"\n\033[1;32m[🎙️ LISTENING ({duration}s)]...\033[0m")
    subprocess.run(f"termux-microphone-record -d -f '{RAW_AUDIO}' 2>/dev/null || true", shell=True)
    time.sleep(duration)
    subprocess.run("termux-microphone-record -q 2>/dev/null || true", shell=True)

    if not os.path.exists(RAW_AUDIO) or os.path.getsize(RAW_AUDIO) < 600:
        return ""

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {key}"}
    files = {"file": (os.path.basename(RAW_AUDIO), open(RAW_AUDIO, "rb"), "audio/m4a")}
    data = {"model": "whisper-large-v3-turbo", "language": "en"}

    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=10)
        if res.status_code == 200:
            return res.json().get("text", "").strip()
    except Exception:
        pass
    return ""

def run_duplex_loop():
    print("\033[1;36m+===================================================+\033[0m")
    print("\033[1;36m|     HYPEROID // FULL-DUPLEX VOICE SESSION ACTIVE  |\033[0m")
    print("\033[1;36m|          (Say 'terminate' or press Ctrl+C)        |\033[0m")
    print("\033[1;36m+===================================================+\033[0m")
    
    agent_script = os.path.expanduser("~/.hyperoid_agent/auto_agent.py")
    speaker_script = os.path.expanduser("~/.hyperoid_agent/spruce_speaker.py")

    subprocess.Popen([sys.executable, speaker_script, "Voice uplink established. I am listening."])
    time.sleep(2)

    while True:
        try:
            user_text = record_and_transcribe(4)
            if not user_text:
                continue

            print(f"\033[1;33m>> USER VOCALIZED: '{user_text}'\033[0m")
            if any(w in user_text.lower() for w in ["terminate", "stop session", "exit voice", "goodbye"]):
                subprocess.Popen([sys.executable, speaker_script, "Terminating voice mode. Systems standby."])
                break

            res = subprocess.run([sys.executable, agent_script, "--headless", user_text], capture_output=True, text=True, timeout=45)
            output = res.stdout.strip()
            print(f"\033[1;32m[HYPEROID_REPORT] >>\033[0m\n{output}\n")
            time.sleep(0.5)

        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    run_duplex_loop()
              

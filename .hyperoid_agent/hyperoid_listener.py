#!/usr/bin/env python3
import os
import sys
import time
import json
import requests
import subprocess

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
CACHE_DIR = os.path.expanduser("~/.hyperoid_agent/cache")
HOTWORD_AUDIO = os.path.join(CACHE_DIR, "hotword.m4a")
CMD_AUDIO = os.path.join(CACHE_DIR, "hotword_cmd.m4a")
os.makedirs(CACHE_DIR, exist_ok=True)

def load_groq_key():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: cfg = json.load(f)
        except Exception: pass
    return os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")

def transcribe_clip(audio_path):
    key = load_groq_key()
    if not key or not os.path.exists(audio_path) or os.path.getsize(audio_path) < 400:
        return ""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/m4a")}
            data = {"model": "whisper-large-v3-turbo", "language": "en"}
            res = requests.post(url, headers=headers, files=files, data=data, timeout=8)
            if res.status_code == 200:
                return res.json().get("text", "").strip().lower()
    except Exception:
        pass
    return ""

def listen_slice(duration=2.5, out_file=HOTWORD_AUDIO):
    if os.path.exists(out_file):
        try: os.remove(out_file)
        except Exception: pass
    subprocess.run(f"termux-microphone-record -d -f '{out_file}' 2>/dev/null || true", shell=True)
    time.sleep(duration)
    subprocess.run("termux-microphone-record -q 2>/dev/null || true", shell=True)

def run_hotword_sentinel():
    agent_script = os.path.expanduser("~/.hyperoid_agent/auto_agent.py")
    speaker_script = os.path.expanduser("~/.hyperoid_agent/spruce_speaker.py")

    while True:
        try:
            listen_slice(2.5, HOTWORD_AUDIO)
            snippet = transcribe_clip(HOTWORD_AUDIO)

            if any(w in snippet for w in ["hyperoid", "hyperroid", "android", "peroid"]):
                subprocess.Popen("termux-vibrate -d 100 2>/dev/null || true", shell=True)
                subprocess.Popen([sys.executable, speaker_script, "Online. Listening."])
                time.sleep(1.2)

                listen_slice(5.0, CMD_AUDIO)
                command_text = transcribe_clip(CMD_AUDIO)

                if command_text:
                    clean_cmd = command_text.replace("hyperoid", "").replace("hyperroid", "").strip()
                    if clean_cmd:
                        subprocess.run([sys.executable, agent_script, "--headless", f"-r {clean_cmd}"], timeout=45)
                time.sleep(1)
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    run_hotword_sentinel()
  

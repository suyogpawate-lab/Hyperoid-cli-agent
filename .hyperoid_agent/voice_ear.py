#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import subprocess

CONFIG_PATH = os.path.expanduser("~/.hyperoid_agent/config.json")
CACHE_DIR = os.path.expanduser("~/.hyperoid_agent/cache")
os.makedirs(CACHE_DIR, exist_ok=True)
RAW_AUDIO = os.path.join(CACHE_DIR, "input.m4a")

def load_groq_key():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f: cfg = json.load(f)
        except Exception: pass
    return os.getenv("GROQ_API_KEY") or cfg.get("GROQ_API_KEY", "")

def record_and_transcribe(duration=5):
    key = load_groq_key()
    if not key:
        print("[!] Missing GROQ_API_KEY for Whisper.")
        return ""

    if os.path.exists(RAW_AUDIO):
        os.remove(RAW_AUDIO)

    print(f"\033[1;32m[🎙️ LISTENING ({duration}s)] Speak now...\033[0m")
    subprocess.run(f"termux-microphone-record -d -f '{RAW_AUDIO}' 2>/dev/null || true", shell=True)
    time.sleep(duration)
    subprocess.run("termux-microphone-record -q 2>/dev/null || true", shell=True)

    if not os.path.exists(RAW_AUDIO) or os.path.getsize(RAW_AUDIO) < 500:
        print("\033[1;31m[!] No audio captured.\033[0m")
        return ""

    print("\033[1;33m[+] Transcribing via Whisper-Turbo...\033[0m")
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {key}"}
    files = {"file": (os.path.basename(RAW_AUDIO), open(RAW_AUDIO, "rb"), "audio/m4a")}
    data = {"model": "whisper-large-v3-turbo", "language": "en"}

    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=12)
        if res.status_code == 200:
            text = res.json().get("text", "").strip()
            print(f"\033[1;36m[✓] INGESTED: '{text}'\033[0m")
            return text
        else:
            print(f"[!] Whisper Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[!] Ingestion error: {e}")
    return ""

if __name__ == "__main__":
    dur = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    transcription = record_and_transcribe(dur)
    if transcription:
        with open(os.path.join(CACHE_DIR, "last_voice_cmd.txt"), "w") as f:
            f.write(transcription)
  

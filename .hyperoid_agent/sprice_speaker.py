#!/usr/bin/env python3
import sys
import os
import asyncio
import edge_tts
import subprocess

CACHE_DIR = os.path.expanduser("~/.hyperoid_agent/cache")
os.makedirs(CACHE_DIR, exist_ok=True)
VOICE_FILE = os.path.join(CACHE_DIR, "speech.mp3")

VOICE_NAME = "en-US-ChristopherNeural"

async def generate_and_play(text):
    clean_text = text.replace('"', '').replace("'", "").strip()
    if not clean_text:
        return
    try:
        communicate = edge_tts.Communicate(clean_text, VOICE_NAME, rate="-4%", pitch="-2Hz")
        await communicate.save(VOICE_FILE)
        subprocess.run(
            f"mpv --no-terminal --really-quiet '{VOICE_FILE}' 2>/dev/null || termux-media-player play '{VOICE_FILE}' >/dev/null 2>&1",
            shell=True
        )
    except Exception:
        subprocess.Popen(f"termux-tts-speak '{clean_text}' 2>/dev/null || true", shell=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text_input = " ".join(sys.argv[1:])
        asyncio.run(generate_and_play(text_input))
                            

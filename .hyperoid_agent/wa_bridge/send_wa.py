#!/usr/bin/env python3
import sys
import json
import time
import os

QUEUE_DIR = os.path.expanduser("~/.hyperoid_agent/wa_bridge/queue")
os.makedirs(QUEUE_DIR, exist_ok=True)

if len(sys.argv) < 3:
    print("[!] Usage: send_wa.py <phone_number> <message_text>")
    sys.exit(1)

phone = sys.argv[1]
text = " ".join(sys.argv[2:])

payload = {
    "phone": phone,
    "text": text,
    "timestamp": time.time()
}

msg_id = f"msg_{int(time.time() * 1000)}.json"
msg_path = os.path.join(QUEUE_DIR, msg_id)

with open(msg_path, "w") as f:
    json.dump(payload, f)

print(f"[✓] Queued background WhatsApp dispatch to +{phone}")


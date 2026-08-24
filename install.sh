#!/bin/bash

set -e

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

clear
echo -e "${CYAN}+===========================================================+${NC}"
echo -e "${CYAN}|         HYPEROID // AUTONOMOUS AGENT DEPLOYMENT           |${NC}"
echo -e "${CYAN}|                LEVEL-9 CYBERDECK INSTALLER                |${NC}"
echo -e "${CYAN}+===========================================================+${NC}"
echo -e "${CYAN} ---THIS OPERATION MAY TAKE UPTO 20 MINUTES DEPENDING ON DEVICE AND INTERNET---${NC}"
echo ""

echo -e "${YELLOW}[1/7] Updating core repositories...${NC}"
pkg update -y

echo -e "${YELLOW}[2/7] Installing core binaries and system packages...${NC}"
pkg install -y \
    python \
    python-pip \
    python-cryptography \
    git \
    tmux \
    termux-api \
    mpv \
    ffmpeg \
    nmap \
    net-tools \
    iproute2 \
    cronie \
    jq \
    bc \
    sqlite \
    nodejs-lts \
    openssh \
    curl

echo -e "${YELLOW}[3/7] Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel --no-cache-dir
pip install \
    requests \
    beautifulsoup4 \
    edge-tts \
    pypdf \
    flask \
    flask-cors \
    python-telegram-bot \
    --prefer-binary --no-cache-dir

echo -e "${YELLOW}[4/7] Initializing agent directory structure & Baileys Bridge...${NC}"
mkdir -p "$HOME/.hyperoid_agent/cache"
mkdir -p "$HOME/.hyperoid_agent/vault"
mkdir -p "$HOME/.hyperoid_agent/sandbox"
mkdir -p "$HOME/.hyperoid_agent/crontabs"
mkdir -p "$HOME/.hyperoid_agent/skills"
mkdir -p "$HOME/.hyperoid_agent/hosted_apps"
mkdir -p "$HOME/.hyperoid_agent/tunnels"
mkdir -p "$HOME/.hyperoid_agent/wa_bridge/auth_info"
mkdir -p "$HOME/.hyperoid_agent/wa_bridge/queue"

# Setup Node package for background WhatsApp bridge
cat << 'PKG_EOF' > "$HOME/.hyperoid_agent/wa_bridge/package.json"
{
  "name": "hyperoid-wa-bridge",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@whiskeysockets/baileys": "^6.7.12",
    "qrcode-terminal": "^0.12.0",
    "pino": "^9.0.0"
  }
}
PKG_EOF

cd "$HOME/.hyperoid_agent/wa_bridge" && npm install --silent

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$REPO_DIR/.hyperoid_agent" ]; then
    echo -e "${YELLOW}[+] Deploying repository files...${NC}"
    cp -r "$REPO_DIR/.hyperoid_agent/"* "$HOME/.hyperoid_agent/" 2>/dev/null || true
fi

chmod +x "$HOME/.hyperoid_agent"/*.py 2>/dev/null || true
chmod +x "$HOME/.hyperoid_agent"/*.sh 2>/dev/null || true
chmod +x "$HOME/.hyperoid_agent/wa_bridge"/*.py 2>/dev/null || true

echo -e "${YELLOW}[5/7] Configuring API & Communication Credentials...${NC}"
CONFIG_FILE="$HOME/.hyperoid_agent/config.json"
CURRENT_KEY=""
CURRENT_GMAIL=""
CURRENT_APP_PASS=""

if [ -f "$CONFIG_FILE" ]; then
    CURRENT_KEY=$(grep -o '"GROQ_API_KEY": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4 || echo "")
    CURRENT_GMAIL=$(grep -o '"GMAIL_USER": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4 || echo "")
    CURRENT_APP_PASS=$(grep -o '"GMAIL_APP_PASS": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4 || echo "")
fi

if [ -n "$CURRENT_KEY" ]; then
    MASKED_KEY="${CURRENT_KEY:0:6}...${CURRENT_KEY: -4}"
    echo -e "${GREEN}[*] Existing Groq API Key detected (${MASKED_KEY}).${NC}"
    read -p "Do you want to update it? (y/N): " UPDATE_CHOICE
    if [[ "$UPDATE_CHOICE" =~ ^[Yy]$ ]]; then
        read -p "Enter your GROQ API Key (gsk_...): " USER_GROQ_KEY
        USER_GROQ_KEY=$(echo "$USER_GROQ_KEY" | tr -d "'\"[:space:]")
    else
        USER_GROQ_KEY="$CURRENT_KEY"
    fi
else
    echo ""
    echo -e "${CYAN}-----------------------------------------------------------${NC}"
    while [ -z "$USER_GROQ_KEY" ]; do
        read -p "Enter your GROQ API Key (gsk_...): " USER_GROQ_KEY
        USER_GROQ_KEY=$(echo "$USER_GROQ_KEY" | tr -d "'\"[:space:]")
        if [ -z "$USER_GROQ_KEY" ]; then
            echo -e "${RED}[!] Key cannot be empty. Please enter a valid key.${NC}"
        fi
    done
    echo -e "${CYAN}-----------------------------------------------------------${NC}"
fi

cat << CFG > "$CONFIG_FILE"
{
  "GROQ_API_KEY": "$USER_GROQ_KEY",
  "GMAIL_USER": "$CURRENT_GMAIL",
  "GMAIL_APP_PASS": "$CURRENT_APP_PASS",
  "TELEGRAM_BOT_TOKEN": "",
  "TELEGRAM_ADMIN_ID": ""
}
CFG

echo -e "${GREEN}[✓] Configuration stored in ~/.hyperoid_agent/config.json${NC}"

echo -e "${YELLOW}[6/7] Deploying WhatsApp Bridge Scripts...${NC}"
cat << 'WA_DAEMON_EOF' > "$HOME/.hyperoid_agent/wa_bridge/wa_daemon.js"
import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import pino from 'pino';
import fs from 'fs';
import path from 'path';

const AUTH_DIR = path.resolve(process.env.HOME, '.hyperoid_agent/wa_bridge/auth_info');
const CMD_QUEUE_DIR = path.resolve(process.env.HOME, '.hyperoid_agent/wa_bridge/queue');

if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true });
if (!fs.existsSync(CMD_QUEUE_DIR)) fs.mkdirSync(CMD_QUEUE_DIR, { recursive: true });

let sock;

async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n\x1b[1;36m+===================================================+\x1b[0m');
            console.log('\x1b[1;36m|     SCAN THIS QR CODE IN WHATSAPP LINKED DEVICES   |\x1b[0m');
            console.log('\x1b[1;36m+===================================================+\x1b[0m\n');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            if (shouldReconnect) {
                setTimeout(startWhatsApp, 3000);
            }
        }
    });

    sock.ev.on('creds.update', saveCreds);
}

setInterval(async () => {
    if (!sock) return;
    try {
        const files = fs.readdirSync(CMD_QUEUE_DIR);
        for (const file of files) {
            if (file.endsWith('.json')) {
                const filePath = path.join(CMD_QUEUE_DIR, file);
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                const jid = `${data.phone.replace(/[^0-9]/g, '')}@s.whatsapp.net`;
                await sock.sendMessage(jid, { text: data.text });
                fs.unlinkSync(filePath);
            }
        }
    } catch (err) {}
}, 1000);

startWhatsApp();
WA_DAEMON_EOF

cat << 'SEND_WA_EOF' > "$HOME/.hyperoid_agent/wa_bridge/send_wa.py"
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
SEND_WA_EOF

chmod +x "$HOME/.hyperoid_agent/wa_bridge/send_wa.py"

echo -e "${YELLOW}[7/7] Registering global 'hud' system launcher...${NC}"
cat << 'HUD_EOF' > "$PREFIX/bin/hud"
#!/bin/bash
pkill -9 -f "python3.*auto_agent.py" 2>/dev/null || true
pkill -9 -f "python3.*hyperoid_listener.py" 2>/dev/null || true
pkill -9 -f "hud_status.sh" 2>/dev/null || true
pkill -9 -f "wa_daemon.js" 2>/dev/null || true
tmux kill-session -t hyperoid 2>/dev/null || true
tmux kill-server 2>/dev/null || true

python3 "$HOME/.hyperoid_agent/sentinel_daemon.py" >/dev/null 2>&1 &
python3 "$HOME/.hyperoid_agent/web_deck.py" >/dev/null 2>&1 &
python3 "$HOME/.hyperoid_agent/hyperoid_listener.py" >/dev/null 2>&1 &
crond 2>/dev/null || true
node "$HOME/.hyperoid_agent/wa_bridge/wa_daemon.js" >/dev/null 2>&1 &

tmux new-session -d -s hyperoid -n "CYBERDECK" "bash $HOME/.hyperoid_agent/hud_status.sh"
tmux split-window -h -t hyperoid:0 "bash -c 'python3 $HOME/.hyperoid_agent/auto_agent.py; echo -e \"\n\033[1;31m[!] AGENT TERMINATED\033[0m Press Enter to drop to shell...\"; read; exec bash'"
tmux select-layout -t hyperoid:0 even-horizontal
tmux select-pane -t hyperoid:0.1
tmux attach-session -t hyperoid
HUD_EOF

chmod +x "$PREFIX/bin/hud"

echo ""
echo -e "${GREEN}+===========================================================+${NC}"
echo -e "${GREEN}|        [✓] HYPEROID OS INSTALLATION COMPLETE              |${NC}"
echo -e "${GREEN}+===========================================================+${NC}"
echo -e "${CYAN}Run 'node ~/.hyperoid_agent/wa_bridge/wa_daemon.js' once to link WhatsApp.${NC}"
echo -e "${CYAN}Type 'hud' to start the cyberdeck interface.${NC}"

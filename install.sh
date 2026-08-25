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
echo -e "${CYAN}+===========================================================+${NC}\n"
echo -e "${CYAN}———THIS OPERATION MAY TAKE UPTO 20 MINUTES———${NC}\n"

echo -e "${YELLOW}[1/6] Updating core repositories & packages...${NC}"
pkg update -y
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

echo -e "${YELLOW}[2/6] Installing Python dependencies...${NC}"
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

echo -e "${YELLOW}[3/6] Setting up directory hierarchy...${NC}"
mkdir -p "$HOME/.hyperoid_agent/cache"
mkdir -p "$HOME/.hyperoid_agent/vault"
mkdir -p "$HOME/.hyperoid_agent/sandbox"
mkdir -p "$HOME/.hyperoid_agent/crontabs"
mkdir -p "$HOME/.hyperoid_agent/skills"
mkdir -p "$HOME/.hyperoid_agent/hosted_apps"
mkdir -p "$HOME/.hyperoid_agent/tunnels"
mkdir -p "$HOME/.hyperoid_agent/wa_bridge/auth_info"
mkdir -p "$HOME/.hyperoid_agent/wa_bridge/queue"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$REPO_DIR/.hyperoid_agent" ]; then
    echo -e "${YELLOW}[+] Deploying repository files...${NC}"
    cp -r "$REPO_DIR/.hyperoid_agent/"* "$HOME/.hyperoid_agent/" 2>/dev/null || true
fi

echo -e "${YELLOW}[4/6] Initializing WhatsApp Baileys Bridge dependencies...${NC}"
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

echo -e "${YELLOW}[5/6] Configuring API credentials...${NC}"
CONFIG_FILE="$HOME/.hyperoid_agent/config.json"
CURRENT_KEY=""

if [ -f "$CONFIG_FILE" ]; then
    CURRENT_KEY=$(grep -o '"GROQ_API_KEY": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4 || echo "")
fi

if [ -n "$CURRENT_KEY" ]; then
    MASKED_KEY="${CURRENT_KEY:0:6}...${CURRENT_KEY: -4}"
    echo -e "${GREEN}[*] Existing Groq API Key found (${MASKED_KEY}).${NC}"
    read -p "Do you want to update it? (y/N): " UPDATE_CHOICE
    if [[ "$UPDATE_CHOICE" =~ ^[Yy]$ ]]; then
        read -p "Enter your Groq API Key: " USER_GROQ_KEY
        USER_GROQ_KEY=$(echo "$USER_GROQ_KEY" | tr -d "'\"[:space:]")
    else
        USER_GROQ_KEY="$CURRENT_KEY"
    fi
else
    while [ -z "$USER_GROQ_KEY" ]; do
        read -p "Enter your Groq API Key (gsk_...): " USER_GROQ_KEY
        USER_GROQ_KEY=$(echo "$USER_GROQ_KEY" | tr -d "'\"[:space:]")
    done
fi

cat << CFG > "$CONFIG_FILE"
{
  "GROQ_API_KEY": "$USER_GROQ_KEY",
  "GMAIL_USER": "",
  "GMAIL_APP_PASS": "",
  "TELEGRAM_BOT_TOKEN": "",
  "TELEGRAM_ADMIN_ID": ""
}
CFG

chmod +x "$HOME/.hyperoid_agent"/*.py 2>/dev/null || true
chmod +x "$HOME/.hyperoid_agent"/*.sh 2>/dev/null || true
chmod +x "$HOME/.hyperoid_agent/wa_bridge"/*.py 2>/dev/null || true

echo -e "${YELLOW}[6/6] Generating 'hud' global command...${NC}"
cat << 'HUD_EOF' > "$PREFIX/bin/hud"
#!/bin/bash
pkill -9 -f "python3.*auto_agent.py" 2>/dev/null || true
pkill -9 -f "hud_status.sh" 2>/dev/null || true
pkill -9 -f "wa_daemon.js" 2>/dev/null || true
tmux kill-session -t hyperoid 2>/dev/null || true
tmux kill-server 2>/dev/null || true

crond 2>/dev/null || true
node "$HOME/.hyperoid_agent/wa_bridge/wa_daemon.js" >/dev/null 2>&1 &

tmux new-session -d -s hyperoid -n "CYBERDECK" "bash $HOME/.hyperoid_agent/hud_status.sh"
tmux split-window -h -t hyperoid:0 "bash -c 'python3 $HOME/.hyperoid_agent/auto_agent.py; echo -e \"\n\033[1;31m[!] AGENT TERMINATED\033[0m Press Enter to drop to shell...\"; read; exec bash'"
tmux select-layout -t hyperoid:0 even-horizontal
tmux select-pane -t hyperoid:0.1
tmux attach-session -t hyperoid
HUD_EOF

chmod +x "$PREFIX/bin/hud"

echo -e "\n${GREEN}+===========================================================+${NC}"
echo -e "${GREEN}|       [✓] HYPEROID OS INSTALLATION SUCCESSFUL             |${NC}"
echo -e "${GREEN}+===========================================================+${NC}"
echo -e "${CYAN}Type 'hud' to start the system.${NC}"

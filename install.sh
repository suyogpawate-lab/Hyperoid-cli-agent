#!/bin/bash

# ==============================================================================
# HYPEROID // LEVEL-8 AUTONOMOUS CYBERDECK OS INSTALLER
# Target Platform: Android / Termux
# ==============================================================================

set -e

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

clear
echo -e "${CYAN}+===========================================================+${NC}"
echo -e "${CYAN}|         HYPEROID // AUTONOMOUS AGENT DEPLOYMENT           |${NC}"
echo -e "${CYAN}|                LEVEL-8 CYBERDECK INSTALLER                |${NC}"
echo -e "${CYAN}+===========================================================+${NC}"
echo ""

# 1. Update Termux Package Repositories
echo -e "${YELLOW}[1/6] Updating Termux core packages...${NC}"
pkg update -y && pkg upgrade -y

# 2. Install System Dependencies
echo -e "${YELLOW}[2/6] Installing hardware tools, audio drivers, and recon binaries...${NC}"
pkg install -y \
    python \
    python-pip \
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
    libxml2 \
    libxslt

# 3. Install Python Dependencies
echo -e "${YELLOW}[3/6] Installing neural TTS, RAG, and Web C2 Python libraries...${NC}"
pip install \
    requests \
    beautifulsoup4 \
    edge-tts \
    pypdf \
    flask \
    flask-cors \
    cryptography \
    python-telegram-bot \
    --quiet

# 4. Initialize Directory Architecture
echo -e "${YELLOW}[4/6] Initializing agent folder hierarchy...${NC}"
mkdir -p "$HOME/.hyperoid_agent/cache"
mkdir -p "$HOME/.hyperoid_agent/vault"
mkdir -p "$HOME/.hyperoid_agent/sandbox"
mkdir -p "$HOME/.hyperoid_agent/crontabs"

# If cloned from git, sync files to ~/.hyperoid_agent
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$REPO_DIR/.hyperoid_agent" ]; then
    echo -e "${YELLOW}[+] Deploying agent scripts from repository...${NC}"
    cp -r "$REPO_DIR/.hyperoid_agent/"* "$HOME/.hyperoid_agent/" 2>/dev/null || true
fi

# Set executable permissions
chmod +x "$HOME/.hyperoid_agent"/*.py 2>/dev/null || true
chmod +x "$HOME/.hyperoid_agent"/*.sh 2>/dev/null || true

# 5. Create Default Configuration if Missing
if [ ! -f "$HOME/.hyperoid_agent/config.json" ]; then
    echo -e "${YELLOW}[5/6] Creating default configuration (~/.hyperoid_agent/config.json)...${NC}"
    cat << 'EOF' > "$HOME/.hyperoid_agent/config.json"
{
  "GROQ_API_KEY": "",
  "TELEGRAM_BOT_TOKEN": "",
  "TELEGRAM_ADMIN_ID": ""
}
EOF
    echo -e "${GREEN}[✓] Config template created.${NC}"
else
    echo -e "${GREEN}[5/6] Existing configuration found. Skipping overwrite.${NC}"
fi

# 6. Configure HUD Command Alias in .bashrc
echo -e "${YELLOW}[6/6] Configuring global 'hud' launch command...${NC}"

cat << 'EOF' > "$PREFIX/bin/hud"
#!/bin/bash
pkill -9 -f "python3.*auto_agent.py" 2>/dev/null || true
tmux kill-server 2>/dev/null || true

# Start background daemons
python3 "$HOME/.hyperoid_agent/sentinel_daemon.py" >/dev/null 2>&1 &
python3 "$HOME/.hyperoid_agent/web_deck.py" >/dev/null 2>&1 &
crond 2>/dev/null || true

# Create tmux split window layout
tmux new-session -d -s hyperoid "bash '$HOME/.hyperoid_agent/hud_status.sh'"
tmux split-window -h -t hyperoid:0.0 "python3 '$HOME/.hyperoid_agent/auto_agent.py'"
tmux select-layout -t hyperoid:0 tiled
tmux attach-session -t hyperoid
EOF

chmod +x "$PREFIX/bin/hud"

echo ""
echo -e "${GREEN}+===========================================================+${NC}"
echo -e "${GREEN}|        [✓] HYPEROID OS INSTALLATION COMPLETE              |${NC}"
echo -e "${GREEN}+===========================================================+${NC}"
echo -e "${CYAN}Next Steps:${NC}"
echo -e " 1. Ensure your GROQ API key is present in: ${YELLOW}~/.hyperoid_agent/config.json${NC}"
echo -e " 2. Launch the full cyberdeck HUD anytime by typing: ${GREEN}hud${NC}"
echo ""

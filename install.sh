#!/bin/bash

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

clear
echo -e "${CYAN}+===========================================================+${NC}"
echo -e "${CYAN}|         HYPEROID // AUTONOMOUS AGENT DEPLOYMENT           |${NC}"
echo -e "${CYAN}|                UNIVERSAL HYBRID INSTALLER                 |${NC}"
echo -e "${CYAN}+===========================================================+${NC}"
echo ""

# 1. Detect Package Manager & Environment
if command -v pkg >/dev/null 2>&1; then
    PKG_MGR="pkg"
    PIP_FLAGS="--prefer-binary --quiet"
elif command -v apt-get >/dev/null 2>&1; then
    PKG_MGR="apt"
    PIP_FLAGS="--break-system-packages --prefer-binary --quiet"
else
    echo -e "${RED}[!] Unsupported package manager. Please run in Termux or Debian/Ubuntu.${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Detected Environment: ${GREEN}${PKG_MGR^^}${YELLOW} ... Updating core repositories...${NC}"
if [ "$PKG_MGR" = "pkg" ]; then
    pkg update -y && pkg upgrade -y
else
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y && apt-get upgrade -y
fi

echo -e "${YELLOW}[2/6] Installing build toolchains, native libraries & binaries...${NC}"
if [ "$PKG_MGR" = "pkg" ]; then
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
        nodejs-lts \
        openssh \
        curl \
        clang \
        make \
        binutils \
        libffi \
        openssl \
        rust \
        tur-repo 2>/dev/null || true
    pkg install -y python-cryptography 2>/dev/null || true
else
    apt-get install -y \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3-dev \
        git \
        tmux \
        mpv \
        ffmpeg \
        nmap \
        net-tools \
        iproute2 \
        cron \
        jq \
        bc \
        sqlite3 \
        nodejs \
        openssh-client \
        curl \
        build-essential \
        libffi-dev \
        libssl-dev 2>/dev/null || true
fi

echo -e "${YELLOW}[3/6] Bootstrapping Python dependencies...${NC}"
pip3 install --upgrade pip setuptools wheel $PIP_FLAGS 2>/dev/null || pip install --upgrade pip setuptools wheel $PIP_FLAGS 2>/dev/null || true

pip_packages=(
    requests
    beautifulsoup4
    edge-tts
    pypdf
    flask
    flask-cors
    cryptography
    python-telegram-bot
    fastapi
    uvicorn
)

pip3 install "${pip_packages[@]}" $PIP_FLAGS || pip install "${pip_packages[@]}" $PIP_FLAGS

echo -e "${YELLOW}[4/6] Initializing agent directory structure...${NC}"
mkdir -p "$HOME/.hyperoid_agent/cache"
mkdir -p "$HOME/.hyperoid_agent/vault"
mkdir -p "$HOME/.hyperoid_agent/sandbox"
mkdir -p "$HOME/.hyperoid_agent/crontabs"
mkdir -p "$HOME/.hyperoid_agent/skills"
mkdir -p "$HOME/.hyperoid_agent/hosted_apps"
mkdir -p "$HOME/.hyperoid_agent/tunnels"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$REPO_DIR/.hyperoid_agent" ]; then
    echo -e "${YELLOW}[+] Deploying agent scripts...${NC}"
    cp -r "$REPO_DIR/.hyperoid_agent/"* "$HOME/.hyperoid_agent/" 2>/dev/null || true
fi

chmod +x "$HOME/.hyperoid_agent"/*.py 2>/dev/null || true
chmod +x "$HOME/.hyperoid_agent"/*.sh 2>/dev/null || true

if [ ! -f "$HOME/.hyperoid_agent/config.json" ]; then
    cat << 'EOF' > "$HOME/.hyperoid_agent/config.json"
{
  "GROQ_API_KEY": "",
  "TELEGRAM_BOT_TOKEN": "",
  "TELEGRAM_ADMIN_ID": ""
}
EOF
fi

echo -e "${YELLOW}[5/6] Registering global 'hud' command...${NC}"
BIN_DIR="/data/data/com.termux/files/usr/bin"
[ ! -d "$BIN_DIR" ] && BIN_DIR="/usr/local/bin"

cat << 'EOF' > "$BIN_DIR/hud"
#!/bin/bash
pkill -9 -f "python3.*auto_agent.py" 2>/dev/null || true
pkill -9 -f "python3.*hyperoid_listener.py" 2>/dev/null || true
pkill -9 -f "hud_status.sh" 2>/dev/null || true
tmux kill-session -t hyperoid 2>/dev/null || true
tmux kill-server 2>/dev/null || true

python3 "$HOME/.hyperoid_agent/sentinel_daemon.py" >/dev/null 2>&1 &
python3 "$HOME/.hyperoid_agent/web_deck.py" >/dev/null 2>&1 &
python3 "$HOME/.hyperoid_agent/hyperoid_listener.py" >/dev/null 2>&1 &
crond 2>/dev/null || cron 2>/dev/null || true

tmux new-session -d -s hyperoid -n "CYBERDECK" "bash $HOME/.hyperoid_agent/hud_status.sh"
tmux split-window -h -t hyperoid:0 "python3 $HOME/.hyperoid_agent/auto_agent.py"
tmux select-layout -t hyperoid:0 even-horizontal
tmux select-pane -t hyperoid:0.1
tmux attach-session -t hyperoid
EOF

chmod +x "$BIN_DIR/hud"

echo ""
echo -e "${GREEN}+===========================================================+${NC}"
echo -e "${GREEN}|        [✓] HYPEROID OS INSTALLATION COMPLETE              |${NC}"
echo -e "${GREEN}+===========================================================+${NC}"

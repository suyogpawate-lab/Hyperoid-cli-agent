#!/data/data/com.termux/files/usr/bin/bash
set -e

clear
echo -e "\033[1;36m+-------------------------------------------------------------+\033[0m"
echo -e "\033[1;36m|            DEPLOYING HYPEROID CYBERDECK HUD                 |\033[0m"
echo -e "\033[1;36m+-------------------------------------------------------------+\033[0m"

# 1. Prompt for Gemini API Key immediately
CONFIG_DIR="$HOME/.hyperoid_agent"
CONFIG_FILE="$CONFIG_DIR/config.json"
mkdir -p "$CONFIG_DIR"

echo -e "\n\033[1;33m[!] Google Gemini API Key required to initialize neural core.\033[0m"
echo -e "\033[1;30mGet your free API key at: https://aistudio.google.com/\033[0m\n"

GEMINI_KEY=""
while [ ${#GEMINI_KEY} -le 15 ]; do
    read -p "Enter Gemini API Key: " GEMINI_KEY
    if [ ${#GEMINI_KEY} -le 15 ]; then
        echo -e "\033[1;31m[!] Invalid key length. Please enter a valid Gemini API key.\033[0m"
    fi
done

# Save credentials to config.json
echo "{\"GEMINI_API_KEY\": \"$GEMINI_KEY\"}" > "$CONFIG_FILE"
echo -e "\033[1;32m[✓] API Key securely saved to $CONFIG_FILE\033[0m\n"

# 2. Resolve Prefix & Install System Dependencies
if [ -z "$PREFIX" ]; then
    PREFIX="/data/data/com.termux/files/usr"
fi

echo -e "\033[1;33m[+] Installing system packages...\033[0m"
pkg update -y
pkg install tmux python git sox termux-api starship libnghttp2 ca-certificates -y

echo -e "\n\033[1;33m[+] Installing Python dependencies...\033[0m"
pip install requests SpeechRecognition

# 3. Provision workspace files
echo -e "\n\033[1;33m[+] Deploying configuration files...\033[0m"
mkdir -p "$HOME/.config"

cp -r .hyperoid_agent/* "$CONFIG_DIR/"
if [ -f "hollywood_starship.toml" ]; then
    cp hollywood_starship.toml "$HOME/.config/"
fi

chmod +x "$CONFIG_DIR/"*.sh "$CONFIG_DIR/"*.py 2>/dev/null || true

# 4. Link binary to PATH
echo -e "\n\033[1;33m[+] Linking global 'hud' binary...\033[0m"
ln -sf "$CONFIG_DIR/start_hud.sh" "$PREFIX/bin/hud"
chmod +x "$PREFIX/bin/hud"

echo -e "\n\033[1;32m[✓] HYPEROID Cyberdeck installed successfully!\033[0m\n"
sleep 1

exec "$PREFIX/bin/hud"

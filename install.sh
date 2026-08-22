#!/data/data/com.termux/files/usr/bin/bash
set -e

echo -e "\033[1;36m+-------------------------------------------------------------+\033[0m"
echo -e "\033[1;36m|            DEPLOYING HYPEROID CYBERDECK HUD                 |\033[0m"
echo -e "\033[1;36m+-------------------------------------------------------------+\033[0m"

if [ -z "$PREFIX" ]; then
    PREFIX="/data/data/com.termux/files/usr"
fi

echo -e "\n\033[1;33m[+] Installing system packages...\033[0m"
pkg update -y
pkg install tmux python git sox termux-api starship libnghttp2 ca-certificates -y

echo -e "\n\033[1;33m[+] Installing Python requirements...\033[0m"

pip install requests SpeechRecognition

echo -e "\n\033[1;33m[+] Provisioning workspace files...\033[0m"
mkdir -p "$HOME/.hyperoid_agent"
mkdir -p "$HOME/.config"

cp -r .hyperoid_agent/* "$HOME/.hyperoid_agent/"
if [ -f "hollywood_starship.toml" ]; then
    cp hollywood_starship.toml "$HOME/.config/"
fi

chmod +x "$HOME/.hyperoid_agent/"*.sh "$HOME/.hyperoid_agent/"*.py 2>/dev/null || true

echo -e "\n\033[1;33m[+] Registering global 'hud' command...\033[0m"
ln -sf "$HOME/.hyperoid_agent/start_hud.sh" "$PREFIX/bin/hud"
chmod +x "$PREFIX/bin/hud"

echo -e "\n\033[1;32m[✓] Setup complete! Launching HYPEROID HUD...\033[0m\n"
sleep 1

exec "$PREFIX/bin/hud"

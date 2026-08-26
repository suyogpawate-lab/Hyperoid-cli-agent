#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
BASE="$(cd "$(dirname "$0")" && pwd)"
HOME_AGENT="$HOME/.hyperoid_agent"

echo '[+] Hyperoid installer'
pkg update -y
pkg install -y python tmux jq curl iproute2 git termux-api
python -m pip install --upgrade requests beautifulsoup4

mkdir -p "$HOME_AGENT"
cp -f "$BASE/.hyperoid_agent"/*.py "$HOME_AGENT/"
cp -f "$BASE/.hyperoid_agent"/*.sh "$HOME_AGENT/"
mkdir -p "$HOME_AGENT/wa_bridge"
cp -f "$BASE/.hyperoid_agent/wa_bridge"/* "$HOME_AGENT/wa_bridge/"
chmod +x "$HOME_AGENT"/*.py "$HOME_AGENT"/*.sh "$HOME_AGENT/wa_bridge/send_wa.py"

if [ ! -f "$HOME_AGENT/config.json" ]; then
cat > "$HOME_AGENT/config.json" <<'JSON'
{"GROQ_API_KEY":"","MODELS":["openai/gpt-oss-120b","openai/gpt-oss-20b","llama-3.3-70b-versatile","llama-3.1-8b-instant"],"TELEGRAM_BOT_TOKEN":"","TELEGRAM_ADMIN_ID":""}
JSON
fi

cat > "$PREFIX/bin/hy" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
exec bash "$HOME_AGENT/start_hud.sh" "\$@"
EOF

cat > "$PREFIX/bin/agent" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
exec python3 "$HOME_AGENT/auto_agent.py" "\$@"
EOF

cat > "$PREFIX/bin/hud" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
exec bash "$HOME_AGENT/start_hud.sh" "\$@"
EOF

chmod +x "$PREFIX/bin/hy" "$PREFIX/bin/agent" "$PREFIX/bin/hud"

echo '[+] Installed: hy, agent, hud'
echo '[+] Run: hy'
echo '[+] Configure ~/.hyperoid_agent/config.json or export GROQ_API_KEY.'

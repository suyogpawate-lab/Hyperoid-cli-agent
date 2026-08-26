#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
BASE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p .hyperoid_agent
cat > .hyperoid_agent/access_terminal.sh <<'ACCESS_EOF'
#!/data/data/com.termux/files/usr/bin/bash

clear
printf '\033[1;36m+------------------------------------------------+\033[0m\n'
printf '\033[1;36m| SYSTEM OVERRIDE | SECURE TERMINAL LINK 0x8F |  \033[0m\n'
printf '\033[1;36m| STATUS: ROOT ACCESS GRANTED | ENCRYPTION: ACTIVE |\033[0m\n'
printf '\033[1;36m+------------------------------------------------+\033[0m\n\n'
printf '\033[1;36m//SYS.LOC: -- //NODE: -- //TIME: %s\033[0m\n' "$(date '+%H:%M:%S')"
printf '\033[1;32m>> ACCESS/_\033[0m\n'

PS1='\[\033[1;32m\]>> ACCESS/_\[\033[0m\] '
export PS1
exec bash -i
ACCESS_EOF
cat > .hyperoid_agent/start_hud.sh <<'START_EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -u

SESSION="hyperoid"
AGENT_HOME="${HOME}/.hyperoid_agent"

tmux kill-session -t "$SESSION" 2>/dev/null || true

tmux new-session -d -s "$SESSION" -n "HYPEROID" \
  "bash '$AGENT_HOME/access_terminal.sh'"

tmux split-window -h -t "$SESSION:0" \
  "python3 '$AGENT_HOME/auto_agent.py'"

tmux select-layout -t "$SESSION:0" even-horizontal
tmux set-option -t "$SESSION" status off
tmux set-option -t "$SESSION" pane-border-style 'fg=cyan'
tmux set-option -t "$SESSION" pane-active-border-style 'fg=cyan'
tmux select-pane -t "$SESSION:0.1"

exec tmux attach-session -t "$SESSION"
START_EOF
cat > .hyperoid_agent/auto_agent.py <<'AUTO_EOF'
#!/usr/bin/env python3
import os, sys
from core import agent, remember

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        goal = " ".join(sys.argv[2:]).strip()
        print(agent(goal, quiet=True))
        return

    print("\033[1;36m+----------------------------------------------+\033[0m")
    print("\033[1;36m| AUTONOMOUS CYBER INTELLIGENCE // HYPEROID   |\033[0m")
    print("\033[1;36m+----------------------------------------------+\033[0m")
    print("\033[2m[READY] Core online | Tool dispatch active\033[0m")

    while True:
        try:
            s = input("\033[1;32m[AGENT_CMD] > \033[0m").strip()
            if not s:
                continue
            if s.lower() in ("exit", "quit"):
                break
            if s.lower() == "clear":
                os.system("clear")
                continue
            remember("user", s, "operator")
            print(agent(s))
        except (EOFError, KeyboardInterrupt):
            print()
            break

if __name__ == "__main__":
    main()
AUTO_EOF
cat > install.sh <<'INSTALL_EOF'
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
INSTALL_EOF
chmod +x .hyperoid_agent/access_terminal.sh .hyperoid_agent/start_hud.sh install.sh
echo '[+] Hyperoid UI fix applied.'

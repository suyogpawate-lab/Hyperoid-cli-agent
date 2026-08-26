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

#!/data/data/com.termux/files/usr/bin/bash
set -e
SESSION=hyperoid
AGENT="$HOME/.hyperoid_agent/auto_agent.py"
HUD="$HOME/.hyperoid_agent/hud_status.sh"
tmux has-session -t "$SESSION" 2>/dev/null && exec tmux attach -t "$SESSION"
tmux new-session -d -s "$SESSION" -n HYPEROID "bash $HUD"
tmux split-window -h -t "$SESSION:0" "python $AGENT"
tmux select-layout -t "$SESSION:0" even-horizontal
tmux select-pane -t "$SESSION:0.1"
exec tmux attach -t "$SESSION"

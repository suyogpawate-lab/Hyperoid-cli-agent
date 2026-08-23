#!/data/data/com.termux/files/usr/bin/bash

SESSION="HYPEROID_HUD"
tmux kill-session -t $SESSION 2>/dev/null || true

tmux new-session -d -s $SESSION
tmux set-option -g status off
tmux set-option -g pane-border-style fg=colour238
tmux set-option -g pane-active-border-style fg=colour39

# Left Pane: Interactive bash with Starship prompt
tmux send-keys -t $SESSION:0.0 "export STARSHIP_CONFIG=$HOME/.config/hollywood_starship.toml" C-m
tmux send-keys -t $SESSION:0.0 "eval \"\$(starship init bash)\"" C-m
tmux send-keys -t $SESSION:0.0 "clear" C-m

# Right Pane: Autonomous Agent
tmux split-window -h -t $SESSION:0.0
tmux send-keys -t $SESSION:0.1 "python3 $HOME/.hyperoid_agent/auto_agent.py" C-m

tmux select-pane -t $SESSION:0.1
tmux attach-session -t $SESSION

#!/data/data/com.termux/files/usr/bin/bash

SESSION="HYPEROID_HUD"
tmux kill-session -t $SESSION 2>/dev/null || true

tmux new-session -d -s $SESSION
tmux set-option -g status off
tmux set-option -g pane-border-style fg=colour238
tmux set-option -g pane-active-border-style fg=colour39

# Left Pane: Prints header once, sets Starship prompt, clears leak
tmux send-keys -t $SESSION:0.0 "clear; echo -e '\033[1;36m+-----------------------------------------------------+\n| [SYSTEM OVERRIDE] :: SECURE TERMINAL LINK 0x8F      |\n| STATUS: ROOT ACCESS GRANTED | ENCRYPTION: ACTIVE    |\n+-----------------------------------------------------+\033[0m'; export STARSHIP_CONFIG=$HOME/.config/hollywood_starship.toml; eval \"\$(starship init bash)\"" C-m

# Right Pane: Dual-pane split launching the Python Agent
tmux split-window -h -t $SESSION:0.0
tmux send-keys -t $SESSION:0.1 "python3 $HOME/.hyperoid_agent/auto_agent.py" C-m

# Set focus on right agent input pane
tmux select-pane -t $SESSION:0.1
tmux attach-session -t $SESSION

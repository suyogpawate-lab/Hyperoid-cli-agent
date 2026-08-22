#!/data/data/com.termux/files/usr/bin/bash

SESSION="HYPEROID_HUD"
tmux kill-session -t $SESSION 2>/dev/null || true

# 1. Start tmux session
tmux new-session -d -s $SESSION
tmux set-option -g status off
tmux set-option -g pane-border-style fg=colour238
tmux set-option -g pane-active-border-style fg=colour39

# 2. Split window horizontally into Left and Right columns
tmux split-window -h -t $SESSION:0.0

# 3. Create Fixed Top Header for Left side (Height: 5 lines)
tmux split-window -v -b -l 5 -t $SESSION:0.0
tmux send-keys -t $SESSION:0.0 "clear" C-m
tmux send-keys -t $SESSION:0.0 "echo -e '\033[1;36m+-----------------------------------------------------+'" C-m
tmux send-keys -t $SESSION:0.0 "echo -e '| [SYSTEM OVERRIDE] :: SECURE TERMINAL LINK 0x8F      |'" C-m
tmux send-keys -t $SESSION:0.0 "echo -e '| STATUS: ROOT ACCESS GRANTED | ENCRYPTION: ACTIVE    |'" C-m
tmux send-keys -t $SESSION:0.0 "echo -e '+-----------------------------------------------------+\033[0m'" C-m
tmux send-keys -t $SESSION:0.0 "tail -f /dev/null" C-m

# 4. Start Scrolling Shell in Bottom-Left pane
tmux send-keys -t $SESSION:0.1 "export STARSHIP_CONFIG=$HOME/.config/hollywood_starship.toml && eval \"\$(starship init bash)\" && clear" C-m

# 5. Create Fixed Top Header for Right side (Height: 5 lines)
tmux split-window -v -b -l 5 -t $SESSION:0.2
tmux send-keys -t $SESSION:0.2 "clear" C-m
tmux send-keys -t $SESSION:0.2 "echo -e '\033[1;36m+---------------------------------------------------+'" C-m
tmux send-keys -t $SESSION:0.2 "echo -e '|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |'" C-m
tmux send-keys -t $SESSION:0.2 "echo -e '+---------------------------------------------------+\033[0m'" C-m
tmux send-keys -t $SESSION:0.2 "echo -e '\033[1;30m[READY] Neural Link Active .. Model: Gemini-3.6-Flash\033[0m'" C-m
tmux send-keys -t $SESSION:0.2 "tail -f /dev/null" C-m

# 6. Start Scrolling AI Agent in Bottom-Right pane
tmux send-keys -t $SESSION:0.3 "python3 $HOME/.hyperoid_agent/auto_agent.py" C-m

# Focus on the Agent command input pane
tmux select-pane -t $SESSION:0.3
tmux attach-session -t $SESSION

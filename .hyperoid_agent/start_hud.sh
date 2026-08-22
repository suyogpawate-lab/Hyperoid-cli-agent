#!/data/data/com.termux/files/usr/bin/bash

SESSION="HYPEROID_HUD"
tmux kill-session -t $SESSION 2>/dev/null || true

# 1. Write helper display scripts to avoid shell command echo leaks
cat << 'EOF' > "$HOME/.hyperoid_agent/top_left.sh"
#!/bin/bash
clear
echo -e "\033[1;36m+-----------------------------------------------------+"
echo -e "| [SYSTEM OVERRIDE] :: SECURE TERMINAL LINK 0x8F      |"
echo -e "| STATUS: ROOT ACCESS GRANTED | ENCRYPTION: ACTIVE    |"
echo -e "+-----------------------------------------------------+\033[0m"
tail -f /dev/null
EOF

cat << 'EOF' > "$HOME/.hyperoid_agent/top_right.sh"
#!/bin/bash
clear
echo -e "\033[1;36m+---------------------------------------------------+"
echo -e "|     AUTONOMOUS CYBER INTELLIGENCE // HYPEROID     |"
echo -e "+---------------------------------------------------+\033[0m"
echo -e "\033[1;30m[READY] Neural Link Active .. Model: Gemini-3.6-Flash\033[0m"
tail -f /dev/null
EOF

chmod +x "$HOME/.hyperoid_agent/top_left.sh" "$HOME/.hyperoid_agent/top_right.sh"

# 2. Build 4-pane layout
tmux new-session -d -s $SESSION
tmux set-option -g status off
tmux set-option -g pane-border-style fg=colour238
tmux set-option -g pane-active-border-style fg=colour39

# Split Left & Right
tmux split-window -h -t $SESSION:0.0

# Split Top-Left (Fixed Header)
tmux split-window -v -b -l 5 -t $SESSION:0.0
tmux send-keys -t $SESSION:0.0 "bash $HOME/.hyperoid_agent/top_left.sh" C-m

# Bottom-Left: Interactive Starship Shell
tmux send-keys -t $SESSION:0.1 "export STARSHIP_CONFIG=$HOME/.config/hollywood_starship.toml && eval \"\$(starship init bash)\" && clear" C-m

# Split Top-Right (Fixed Header)
tmux split-window -v -b -l 5 -t $SESSION:0.2
tmux send-keys -t $SESSION:0.2 "bash $HOME/.hyperoid_agent/top_right.sh" C-m

# Bottom-Right: Autonomous Agent
tmux send-keys -t $SESSION:0.3 "python3 $HOME/.hyperoid_agent/auto_agent.py" C-m

# Focus agent input
tmux select-pane -t $SESSION:0.3
tmux attach-session -t $SESSION

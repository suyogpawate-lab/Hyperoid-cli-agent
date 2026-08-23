#!/bin/bash

# ==============================================================================
# HYPEROID // TACTICAL CYBERDECK HUD INITIALIZER
# ==============================================================================

# Ensure previous sessions are cleared
pkill -9 -f "python3.*auto_agent.py" 2>/dev/null || true
pkill -9 -f "python3.*sentinel_daemon.py" 2>/dev/null || true
pkill -9 -f "python3.*web_deck.py" 2>/dev/null || true
tmux kill-server 2>/dev/null || true

# Boot background sentinels and web deck
python3 "$HOME/.hyperoid_agent/sentinel_daemon.py" >/dev/null 2>&1 &
python3 "$HOME/.hyperoid_agent/web_deck.py" >/dev/null 2>&1 &
crond 2>/dev/null || true

# Initialize tmux dual-pane HUD layout
tmux new-session -d -s hyperoid "bash '$HOME/.hyperoid_agent/hud_status.sh'"
tmux split-window -h -t hyperoid:0.0 "python3 '$HOME/.hyperoid_agent/auto_agent.py'"

# Balance the terminal split evenly
tmux select-layout -t hyperoid:0 even-horizontal

# Attach to HUD session
tmux attach-session -t hyperoid

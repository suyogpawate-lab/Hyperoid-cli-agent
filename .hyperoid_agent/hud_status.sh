#!/bin/bash
clear
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'
GRAY='\033[1;30m'

while true; do
    clear
    DATE=$(date "+%Y-%m-%d // %H:%M:%S")
    UPTIME=$(uptime -p 2>/dev/null || uptime | awk -F'( |,|:)+' '{print $6" hrs"}')
    
    BATT_JSON=$(termux-battery-status 2>/dev/null)
    if [ -n "$BATT_JSON" ]; then
        PCT=$(echo "$BATT_JSON" | grep -o '"percentage": [0-9]*' | awk '{print $2}')
        STATUS=$(echo "$BATT_JSON" | grep -o '"status": "[^"]*"' | awk -F'"' '{print $4}')
        TEMP=$(echo "$BATT_JSON" | grep -o '"temperature": [0-9.]*' | awk '{print $2}')
    else
        PCT="N/A"; STATUS="DISCHARGING"; TEMP="N/A"
    fi

    IP_ADDR=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}')
    [ -z "$IP_ADDR" ] && IP_ADDR="OFFLINE / ISOLATED"

    STORAGE=$(df -h "$HOME" 2>/dev/null | tail -1 | awk '{print $3"/"$2" ("$5")"}')
    WA_DAEMON=$(pgrep -f "whatsapp_daemon.py" >/dev/null && echo -e "${GREEN}ONLINE:5050${NC}" || echo -e "${RED}OFFLINE${NC}")

    echo -e "${CYAN}+===========================================================+${NC}"
    echo -e "${CYAN}|         HYPEROID // TACTICAL CYBERDECK HUD v4.0           |${NC}"
    echo -e "${CYAN}+===========================================================+${NC}"
    echo -e "${GRAY}SYSTEM CLOCK :${NC} ${GREEN}$DATE${NC}"
    echo -e "${GRAY}NODE UPTIME  :${NC} $UPTIME"
    echo -e "${GRAY}LOCAL INGRESS:${NC} ${YELLOW}$IP_ADDR${NC}"
    echo -e "${GRAY}STORAGE VAULT:${NC} $STORAGE"
    echo -e "${GRAY}WHATSAPP GTWY:${NC} $WA_DAEMON"
    echo ""
    echo -e "${CYAN}--- [ HARDWARE CORE METRICS ] -------------------------------${NC}"
    echo -e "${GRAY}CHARGE LEVEL :${NC} ${GREEN}${PCT}%${NC} [${STATUS}]"
    echo -e "${GRAY}THERMAL PROBE:${NC} ${YELLOW}${TEMP}°C${NC}"
    echo ""
    echo -e "${CYAN}--- [ NEURAL BUS CHANNELS ] ---------------------------------${NC}"
    echo -e "CHANNEL 1 [PRIMARY] : ${GREEN}Groq LPU (qwen3.6-27b / llama-3.3-70b)${NC}"
    echo -e "CHANNEL 2 [MEMORY]  : ${CYAN}SQLite Epistemic Graph Core${NC}"
    echo -e "CHANNEL 3 [INTENTS] : ${YELLOW}Android Activity / Broadcast Subsystem${NC}"
    echo ""
    echo -e "${CYAN}--- [ LIVE TELEMETRY LOGS ] ---------------------------------${NC}"
    if [ -f "$HOME/.hyperoid_agent/agent.log" ]; then
        tail -n 8 "$HOME/.hyperoid_agent/agent.log" | sed 's/^/  /'
    else
        echo -e "${GRAY}  [SYSTEM IDLE - AWAITING USER DIRECTIVES]${NC}"
    fi
    echo -e "${CYAN}+===========================================================+${NC}"
    sleep 2
done


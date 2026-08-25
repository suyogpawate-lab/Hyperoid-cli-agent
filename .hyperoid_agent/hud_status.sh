#!/bin/bash
clear

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

while true; do
    clear
    TIME_STR=$(date +"%H:%M:%S")
    echo -e "${CYAN}//SYS.LOC: ~   //NODE: HYPEROID //TIME: ${TIME_STR}${NC}\n"
    echo -e "${GREEN}>> ACCESS//_${NC}\n"
    
    BATTERY_RAW=$(termux-battery-status 2>/dev/null || echo '{"percentage": 100, "status": "UNKNOWN"}')
    BAT_PCT=$(echo "$BATTERY_RAW" | jq -r '.percentage // 100' 2>/dev/null || echo "N/A")
    BAT_STAT=$(echo "$BATTERY_RAW" | jq -r '.status // "DISCHARGING"' 2>/dev/null || echo "OK")
    IP_ADDR=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' || echo "127.0.0.1")
    
    echo -e "${YELLOW}[TELEMETRY LINK ACTIVE]${NC}"
    echo -e "  - Node Status:    ${GREEN}ONLINE${NC}"
    echo -e "  - Battery Power:  ${BAT_PCT}% (${BAT_STAT})"
    echo -e "  - Active Route:   ${IP_ADDR}"
    
    echo -e "\n${YELLOW}[DAEMON BUS MONITOR]${NC}"
    if pgrep -f "wa_daemon.js" >/dev/null 2>&1; then
        echo -e "  - WA Gateway:     ${GREEN}ONLINE [SOCKET ACTIVE]${NC}"
    else
        echo -e "  - WA Gateway:     ${RED}OFFLINE${NC}"
    fi

    echo -e "\n${CYAN}---------------------------------------------------${NC}"
    echo -e "Ready for operational directives in the right pane."
    echo -e "Press CTRL+C anytime to access standard shell."
    
    sleep 3
done

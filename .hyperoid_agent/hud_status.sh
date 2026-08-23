#!/bin/bash
clear
BLUE='\033[1;34m'
NC='\033[0m'

TIME=$(date "+%H:%M:%S")
echo -e "${BLUE}//SYS.LOC: ~  //NODE: HYPEROID //TIME: ${TIME}${NC}"
echo ""

export PS1="\[\033[1;32m\]>> ACCESS//_ \[\033[0m\]"
exec bash --norc -i

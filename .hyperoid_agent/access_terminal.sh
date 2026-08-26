#!/data/data/com.termux/files/usr/bin/bash

clear
printf '\033[1;36m+------------------------------------------------+\033[0m\n'
printf '\033[1;36m| SYSTEM OVERRIDE | SECURE TERMINAL LINK 0x8F |  \033[0m\n'
printf '\033[1;36m| STATUS: ROOT ACCESS GRANTED | ENCRYPTION: ACTIVE |\033[0m\n'
printf '\033[1;36m+------------------------------------------------+\033[0m\n\n'
printf '\033[1;36m//SYS.LOC: -- //NODE: -- //TIME: %s\033[0m\n' "$(date '+%H:%M:%S')"
printf '\033[1;32m>> ACCESS/_\033[0m\n'

PS1='\[\033[1;32m\]>> ACCESS/_\[\033[0m\] '
export PS1
exec bash -i

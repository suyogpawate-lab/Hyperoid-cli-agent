#!/data/data/com.termux/files/usr/bin/bash
while :; do
  clear
  printf '\033[1;36mHYPEROID // SYSTEM TELEMETRY\033[0m\n\n'
  printf 'TIME       %s\n' "$(date '+%H:%M:%S')"
  printf 'ANDROID    %s\n' "$(getprop ro.build.version.release 2>/dev/null)"
  printf 'DEVICE     %s\n' "$(getprop ro.product.model 2>/dev/null)"
  if command -v termux-battery-status >/dev/null 2>&1; then
    termux-battery-status 2>/dev/null | jq -r '"BATTERY    \(.percentage)% / \(.status)"' 2>/dev/null || true
  fi
  printf 'MEMORY\n'; free -h 2>/dev/null | head -2
  printf '\nREADY\n'
  sleep 3
done

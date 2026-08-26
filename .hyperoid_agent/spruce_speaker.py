#!/usr/bin/env python3
import sys,subprocess
text=' '.join(sys.argv[1:]).strip()
if text: subprocess.run(['termux-tts-speak',text])

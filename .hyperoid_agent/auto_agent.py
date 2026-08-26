#!/usr/bin/env python3
import os, sys, shlex
from core import agent, remember

def main():
    if len(sys.argv)>1 and sys.argv[1]=='--headless':
        goal=' '.join(sys.argv[2:]).strip(); print(agent(goal,quiet=True)); return
    print("HYPEROID // ONLINE")
    while True:
        try:
            s=input("[HYPEROID] > ").strip()
            if not s: continue
            if s.lower() in ('exit','quit'): break
            if s.lower()=='clear': os.system('clear'); continue
            remember('user',s,'operator'); print(agent(s))
        except (EOFError,KeyboardInterrupt): print(); break
if __name__=='__main__': main()

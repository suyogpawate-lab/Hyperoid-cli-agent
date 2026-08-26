#!/usr/bin/env python3
import os, sys
from core import agent, remember

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        goal = " ".join(sys.argv[2:]).strip()
        print(agent(goal, quiet=True))
        return

    print("\033[1;36m+----------------------------------------------+\033[0m")
    print("\033[1;36m| AUTONOMOUS CYBER INTELLIGENCE // HYPEROID   |\033[0m")
    print("\033[1;36m+----------------------------------------------+\033[0m")
    print("\033[2m[READY] Core online | Tool dispatch active\033[0m")

    while True:
        try:
            s = input("\033[1;32m[AGENT_CMD] > \033[0m").strip()
            if not s:
                continue
            if s.lower() in ("exit", "quit"):
                break
            if s.lower() == "clear":
                os.system("clear")
                continue
            remember("user", s, "operator")
            print(agent(s))
        except (EOFError, KeyboardInterrupt):
            print()
            break

if __name__ == "__main__":
    main()

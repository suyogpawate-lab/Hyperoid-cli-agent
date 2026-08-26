#!/usr/bin/env python3
"""Hyperoid core: local tools, memory, and Groq-compatible inference."""
from __future__ import annotations
import json, os, re, shlex, sqlite3, subprocess, sys, time, urllib.parse
from pathlib import Path
from typing import Optional
import requests

HOME = Path(os.path.expanduser("~/.hyperoid_agent"))
CONFIG = HOME / "config.json"
DB = HOME / "memory.db"
SANDBOX = HOME / "sandbox"
SKILLS = HOME / "skills"
CACHE = HOME / "cache"
for p in (HOME, SANDBOX, SKILLS, CACHE): p.mkdir(parents=True, exist_ok=True)

DEFAULT_MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
SYSTEM = """You are Hyperoid, a concise autonomous Termux/Android CLI agent.
Return either one ACTION line or one final ANSWER line per turn.
ACTION syntax: ACTION <tool> <JSON object>
ANSWER syntax: ANSWER <concise result>
Never emit more than one ACTION in a turn. Wait for TOOL_RESULT before the next action.
Available tools: shell, device, apps, launch_app, termux, web_search, nmap, python, speak.
Use shell for ordinary Termux commands. Use device for live Android/Termux information.
Use launch_app only when the user explicitly asks to open/start an Android app.
Be technical, concise, and do not expose hidden reasoning."""


def load_config():
    cfg = {}
    try:
        cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    except Exception:
        pass
    return cfg


def key():
    return os.getenv("GROQ_API_KEY") or load_config().get("GROQ_API_KEY", "")


def models():
    m = load_config().get("MODELS") or os.getenv("HYPEROID_MODELS", "")
    if isinstance(m, list): return [str(x) for x in m if x]
    if m: return [x.strip() for x in str(m).split(",") if x.strip()]
    return DEFAULT_MODELS


def db():
    c = sqlite3.connect(DB, timeout=10)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS episodic_memory(id INTEGER PRIMARY KEY, ts REAL, role TEXT, content TEXT, model TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS knowledge_vault(key TEXT PRIMARY KEY, value TEXT, updated REAL)")
    c.commit(); return c


def remember(role, content, model="local"):
    try:
        c=db(); c.execute("INSERT INTO episodic_memory(ts,role,content,model) VALUES(?,?,?,?)", (time.time(),role,str(content)[:5000],model)); c.commit(); c.close()
    except Exception: pass


def context(limit=8):
    try:
        c=db(); rows=c.execute("SELECT role,content,model FROM episodic_memory ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); c.close()
        return "\n".join(f"[{r}] {x[:700]}" for r,x,_ in reversed(rows)) or "No previous context."
    except Exception: return "No previous context."


def run(cmd, timeout=30, cwd=None):
    try:
        p=subprocess.run(cmd, shell=True, executable=os.environ.get("SHELL", "/bin/sh"), cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out=(p.stdout or "") + (("\nSTDERR:\n"+p.stderr) if p.stderr else "")
        return f"exit={p.returncode}\n{out.strip()[:6000]}"
    except subprocess.TimeoutExpired: return "TIMEOUT"
    except Exception as e: return f"ERROR: {e}"


def device_info():
    cmds = {
      "os": "getprop ro.build.version.release 2>/dev/null",
      "model": "getprop ro.product.model 2>/dev/null",
      "abi": "getprop ro.product.cpu.abi 2>/dev/null",
      "kernel": "uname -a",
      "memory": "free -h 2>/dev/null || cat /proc/meminfo | head",
      "storage": "df -h $HOME 2>/dev/null",
      "network": "ip -brief address 2>/dev/null || ifconfig 2>/dev/null",
      "battery": "termux-battery-status 2>/dev/null",
    }
    return "\n".join(f"[{k}]\n{run(v,8)}" for k,v in cmds.items())


def apps():
    return run("pm list packages 2>/dev/null | sed 's/^package://' | sort", 15)


def launch_app(package):
    package=package.strip()
    if not re.fullmatch(r"[A-Za-z0-9_\.]+", package): return "ERROR: invalid package name"
    return run(f"monkey -p {shlex.quote(package)} -c android.intent.category.LAUNCHER 1 2>&1", 15)


def termux(command):
    if not re.fullmatch(r"termux-[A-Za-z0-9_-]+(?:\s+.*)?", command.strip()):
        return "ERROR: termux tool name required"
    return run(command, 30)


def web_search(q):
    try:
        u="https://html.duckduckgo.com/html/?q="+urllib.parse.quote(q)
        r=requests.get(u,headers={"User-Agent":"Hyperoid/10"},timeout=10)
        from bs4 import BeautifulSoup
        s=BeautifulSoup(r.text,"html.parser")
        items=[]
        for a in s.select("a.result__a")[:5]: items.append(a.get_text(" ",strip=True)+" | "+a.get("href", ""))
        return "\n".join(items) or "No results."
    except Exception as e: return f"SEARCH ERROR: {e}"


def python_run(code, filename="agent_task.py"):
    safe=Path(filename).name
    path=SANDBOX/safe; path.write_text(code)
    return run(f"python {shlex.quote(str(path))}",30)


def execute_tool(name, args):
    if name=="shell": return run(str(args.get("command","")), int(args.get("timeout",30)))
    if name=="device": return device_info()
    if name=="apps": return apps()
    if name=="launch_app": return launch_app(str(args.get("package","")))
    if name=="termux": return termux(str(args.get("command","")))
    if name=="web_search": return web_search(str(args.get("query","")))
    if name=="nmap": return run(f"nmap {args.get('flags','-T4')} {shlex.quote(str(args.get('target','')))}",60)
    if name=="python": return python_run(str(args.get("code","")), str(args.get("filename","agent_task.py")))
    if name=="speak": return run(f"termux-tts-speak {shlex.quote(str(args.get('text','')))}",30)
    return "ERROR: unknown tool"


def parse_action(text):
    m=re.search(r"^ACTION\s+(\w+)\s+(\{.*\})\s*$",text.strip(),re.S|re.I)
    if not m: return None
    try: return m.group(1), json.loads(m.group(2))
    except Exception: return None


def ask(messages):
    k=key()
    if not k: return None, "NO_KEY"
    url="https://api.groq.com/openai/v1/chat/completions"
    last=""
    for model in models():
        for attempt in range(2):
            try:
                r=requests.post(url,headers={"Authorization":f"Bearer {k}"},json={"model":model,"messages":messages,"temperature":0.1,"max_tokens":1200},timeout=30)
                if r.ok:
                    return r.json()["choices"][0]["message"]["content"].strip(), model
                last=f"{model}: HTTP {r.status_code} {r.text[:200]}"
                if r.status_code not in (408,429,500,502,503,504): break
                time.sleep(1.2*(attempt+1))
            except Exception as e: last=f"{model}: {e}"; time.sleep(1)
    return None,last


def agent(goal, max_steps=8, quiet=False):
    msgs=[{"role":"system","content":SYSTEM+"\nContext:\n"+context()}, {"role":"user","content":goal}]
    for step in range(max_steps):
        reply, model=ask(msgs)
        if not reply: return f"ERROR: model unavailable ({model})"
        remember("assistant",reply,model); msgs.append({"role":"assistant","content":reply})
        action=parse_action(reply)
        if not action:
            if reply.upper().startswith("ANSWER "): return reply[7:].strip()
            return reply
        name,args=action
        result=execute_tool(name,args)
        remember("tool",result,"local")
        msgs.append({"role":"user","content":"TOOL_RESULT\n"+result})
        if not quiet: print(f"[tool:{name}] {result[:1000]}")
    return "ERROR: execution depth exceeded"

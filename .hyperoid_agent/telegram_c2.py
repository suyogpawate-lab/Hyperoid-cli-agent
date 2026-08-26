#!/usr/bin/env python3
"""Optional Telegram bridge. Only configured ADMIN_CHAT_ID is accepted."""
import os,json,requests,subprocess,sys,time
from pathlib import Path
C=Path(os.path.expanduser('~/.hyperoid_agent/config.json'))
try: cfg=json.loads(C.read_text())
except: cfg={}
token=os.getenv('TELEGRAM_BOT_TOKEN') or cfg.get('TELEGRAM_BOT_TOKEN',''); admin=str(cfg.get('TELEGRAM_ADMIN_ID',''))
if not token or not admin: raise SystemExit('Telegram disabled: configure TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_ID.')
off=0
while True:
    try:
        r=requests.get(f'https://api.telegram.org/bot{token}/getUpdates',params={'offset':off+1,'timeout':20},timeout=25)
        for u in r.json().get('result',[]):
            off=u['update_id']; m=u.get('message',{}); chat=str(m.get('chat',{}).get('id','')); text=m.get('text','').strip()
            if chat!=admin or not text: continue
            p=subprocess.run([sys.executable,os.path.expanduser('~/.hyperoid_agent/auto_agent.py'),'--headless',text],capture_output=True,text=True,timeout=90)
            requests.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':admin,'text':p.stdout[-3500:] or p.stderr[-3500:]},timeout=10)
    except Exception: time.sleep(2)

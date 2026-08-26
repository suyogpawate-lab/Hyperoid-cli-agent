#!/usr/bin/env python3
import json,subprocess,time,os
while True:
    try:
        p=subprocess.run(['termux-battery-status'],capture_output=True,text=True,timeout=5)
        if p.returncode==0:
            d=json.loads(p.stdout); pct=float(d.get('percentage',100)); temp=float(d.get('temperature',0) or 0)
            if pct<=15 and d.get('status')!='CHARGING': subprocess.run(['termux-notification','-t','Hyperoid','-c',f'Battery {pct:.0f}%'])
            if temp>=45: subprocess.run(['termux-notification','-t','Hyperoid','-c',f'Temperature {temp:.1f} C'])
    except Exception: pass
    time.sleep(15)

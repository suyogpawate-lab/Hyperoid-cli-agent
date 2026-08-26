#!/usr/bin/env python3
import json,os,sys,time
from pathlib import Path
D=Path(os.path.expanduser('~/.hyperoid_agent/wa_bridge/queue')); D.mkdir(parents=True,exist_ok=True)
if len(sys.argv)<3: raise SystemExit('usage: send_wa.py PHONE MESSAGE')
p=D/f'msg_{time.time_ns()}.json'; p.write_text(json.dumps({'phone':sys.argv[1],'text':' '.join(sys.argv[2:]),'timestamp':time.time()})); print(f'queued {p.name}')

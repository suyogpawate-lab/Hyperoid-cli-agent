#!/usr/bin/env python3
import os,sys,time,json,subprocess,requests
from pathlib import Path
HOME=Path(os.path.expanduser('~/.hyperoid_agent')); CACHE=HOME/'cache'; CACHE.mkdir(parents=True,exist_ok=True); AUDIO=CACHE/'input.m4a'
def key():
    try:return os.getenv('GROQ_API_KEY') or json.loads((HOME/'config.json').read_text()).get('GROQ_API_KEY','')
    except:return os.getenv('GROQ_API_KEY','')
def transcribe(seconds=4):
    if AUDIO.exists(): AUDIO.unlink()
    subprocess.run(['termux-microphone-record','-d','-f',str(AUDIO)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(seconds); subprocess.run(['termux-microphone-record','-q'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    k=key()
    if not k or not AUDIO.exists(): return ''
    try:
        with AUDIO.open('rb') as f:r=requests.post('https://api.groq.com/openai/v1/audio/transcriptions',headers={'Authorization':f'Bearer {k}'},files={'file':(AUDIO.name,f,'audio/m4a')},data={'model':'whisper-large-v3-turbo'},timeout=15)
        return r.json().get('text','').strip() if r.ok else ''
    except:return ''
if __name__=='__main__':
    from auto_agent import agent
    while True:
        try:
            t=transcribe();
            if t.lower() in ('exit','quit','terminate'): break
            if t: print(agent(t))
        except KeyboardInterrupt: break

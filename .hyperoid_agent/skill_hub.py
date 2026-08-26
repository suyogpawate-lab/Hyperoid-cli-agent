#!/usr/bin/env python3
import os,re,json
from pathlib import Path
D=Path(os.path.expanduser('~/.hyperoid_agent/skills')); D.mkdir(parents=True,exist_ok=True)
def clean(s): return re.sub(r'[^A-Za-z0-9_-]','-',s.strip().lower()).strip('-')
def list_skills():
    x=sorted(p.stem for p in D.glob('*.md')); return '\n'.join(x) if x else 'No skills installed.'
def get_skill(name):
    p=D/(clean(name)+'.md'); return p.read_text()[:4000] if p.exists() else 'Skill not found.'
def install(name,content=None):
    p=D/(clean(name)+'.md'); p.write_text(content or f'# {name}\n\nSkill placeholder. Add verified operational rules here.\n'); return str(p)
if __name__=='__main__':
    import sys
    a=sys.argv[1:] 
    if not a: print(list_skills())
    elif a[0]=='list_skills': print(list_skills())
    elif a[0]=='get_rules' and len(a)>1: print(get_skill(a[1]))
    elif a[0]=='install_skill' and len(a)>1: print(install(' '.join(a[1:])))

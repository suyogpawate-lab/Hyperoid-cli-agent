#!/usr/bin/env python3
import os,sys,subprocess
from flask import Flask,request,jsonify
app=Flask(__name__)
@app.get('/')
def index(): return '<h2>HYPEROID</h2><p>POST /api/execute with JSON {"command":"..."}</p>'
@app.post('/api/execute')
def execute():
    from core import agent
    cmd=(request.get_json(silent=True) or {}).get('command','').strip()
    return jsonify(reply=agent(cmd,quiet=True))
if __name__=='__main__': app.run(host='127.0.0.1',port=8080,debug=False)

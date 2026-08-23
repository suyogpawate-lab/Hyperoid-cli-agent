#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HYPEROID // CYBERDECK C2</title>
    <style>
        body { background-color: #080a0f; color: #00ffcc; font-family: 'Courier New', monospace; margin: 0; padding: 15px; }
        .grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
        @media(min-width: 768px) { .grid { grid-template-columns: 320px 1fr; } }
        .card { background: #0e131f; border: 1px solid #1a293d; padding: 12px; border-radius: 4px; box-shadow: 0 0 10px rgba(0,255,204,0.05); }
        .title { color: #ff0055; font-weight: bold; border-bottom: 1px solid #1a293d; padding-bottom: 4px; margin-bottom: 8px; font-size: 13px; }
        #logs { height: 420px; overflow-y: auto; background: #05070a; border: 1px solid #141e2e; padding: 10px; font-size: 12px; line-height: 1.4; color: #7cfc00; }
        input[type="text"] { width: 100%; background: #05070a; border: 1px solid #00ffcc; color: #00ffcc; padding: 10px; box-sizing: border-box; font-family: inherit; margin-top: 8px; }
        button { background: #ff0055; color: #fff; border: none; padding: 8px 12px; font-weight: bold; cursor: pointer; margin-top: 6px; }
        .stat { display: flex; justify-content: space-between; margin: 4px 0; font-size: 12px; }
    </style>
</head>
<body>
    <h2 style="margin: 0 0 10px 0; color: #00ffcc; font-size: 18px;">⚡ HYPEROID // WEB CYBERDECK OS</h2>
    <div class="grid">
        <div class="card">
            <div class="title">SYSTEM TELEMETRY</div>
            <div class="stat"><span>STATUS:</span> <span style="color:#7cfc00">ONLINE [L8]</span></div>
            <div class="stat"><span>ENGINE:</span> <span>Groq / Wafer LPU</span></div>
            <div class="stat"><span>VOICE:</span> <span>Neural Spruce</span></div>
            <div class="stat"><span>C2 PORT:</span> <span>8080 (REST/SSE)</span></div>
            <hr style="border: 0; border-top: 1px solid #1a293d;">
            <div class="title">QUICK TRIGGERS</div>
            <button onclick="sendCmd('Check hardware sensors and battery')">SENSORS</button>
            <button onclick="sendCmd('Scan local subnet network')">LAN RECON</button>
            <button onclick="sendCmd('Read last vault memories')">VAULT</button>
        </div>
        <div class="card">
            <div class="title">LIVE TELEMETRY LOGS</div>
            <div id="logs">Connecting to live bus...</div>
            <input type="text" id="cmdInput" placeholder="Enter cyberdeck directive..." onkeydown="if(event.key==='Enter') execute();">
        </div>
    </div>
    <script>
        function log(msg) {
            const el = document.getElementById('logs');
            el.innerHTML += '<div>' + msg + '</div>';
            el.scrollTop = el.scrollHeight;
        }
        function sendCmd(cmd) {
            document.getElementById('cmdInput').value = cmd;
            execute();
        }
        function execute() {
            const input = document.getElementById('cmdInput');
            const val = input.value.trim();
            if(!val) return;
            log('<span style="color:#00ffcc">> ' + val + '</span>');
            input.value = '';
            fetch('/api/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: val})
            }).then(r => r.json()).then(data => {
                log('<span style="color:#7cfc00">' + data.reply.replace(/\\n/g, '<br>') + '</span>');
            }).catch(e => log('<span style="color:#ff0055">Error: ' + e + '</span>'));
        }
        setInterval(() => {
            fetch('/api/ping').then(r => r.json()).then(d => {});
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/ping')
def ping():
    return jsonify({"status": "active", "time": time.time()})

@app.route('/api/execute', methods=['POST'])
def execute():
    cmd = request.json.get("command", "")
    agent = os.path.expanduser("~/.hyperoid_agent/auto_agent.py")
    res = subprocess.run([sys.executable, agent, "--headless", cmd], capture_output=True, text=True, timeout=45)
    return jsonify({"reply": res.stdout.strip() if res.stdout.strip() else "Complete."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
  

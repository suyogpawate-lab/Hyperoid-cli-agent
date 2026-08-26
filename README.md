# Hyperoid CLI Agent

Fast autonomous AI CLI for Termux/Android.

## Install
```bash
git clone https://github.com/suyogpawate-lab/Hyperoid-cli-agent.git
cd Hyperoid-cli-agent
bash install.sh
```

Configure `~/.hyperoid_agent/config.json`:
```json
{"GROQ_API_KEY":"YOUR_KEY","MODELS":["openai/gpt-oss-120b","llama-3.3-70b-versatile","llama-3.1-8b-instant"]}
```

Run anywhere:
```bash
hy
```

Split terminal HUD:
```bash
hud
```

Hyperoid tools include shell execution, live Android/Termux telemetry, installed-package discovery, explicit Android app launching, Termux commands, Python execution, web search, nmap, and TTS.

Optional voice, Telegram and WhatsApp bridges are separate processes and are not started automatically.

### Android limitations
Termux can only access Android capabilities exposed through Termux/Termux:API and permissions granted to it. Background execution of arbitrary third-party apps is controlled by Android and cannot be universally bypassed without elevated privileges.

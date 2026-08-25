# ⚡ HYPEROID // v9 AUTONOMOUS CYBERDECK OS

<p align="center">
  <img src="https://img.shields.io/badge/PLATFORM-Android%2FTermux-00ffcc?style=for-the-badge&logo=android" />
  <img src="https://img.shields.io/badge/CORE-Autonomous%20ReAct%20Swarm-ff0055?style=for-the-badge" />
  <img src="https://img.shields.io/badge/VOICE-ChatGPT%20Spruce%20Neural-7cfc00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/INFERENCE-Groq%20LPU%20Ultra--Fast-blueviolet?style=for-the-badge" />
</p>

HYPEROID is an autonomous tactical cyberdeck operating system and AI agent terminal tailored specifically for Android / Termux. Designed with Hollywood cyberdeck telemetry aesthetics, it transforms an Android tablet or smartphone into a self-reflective, multi-agent AI command post featuring local skill compilation, web server hosting, and zero-config public tunneling.

---

## ⚡ Key Features
## Key Features

* **Multi-Model LLM Swarm Engine**: Autonomous cascading fallback across high-throughput models (`groq/compound`, `openai/gpt-oss-120b`, `qwen/qwen3.6-27b`, and `canopylabs/orpheus`) ensuring zero downtime and dynamic model resolution.
* **Persistent Shared Memory**: SQLite-backed episodic memory and persistent knowledge vault (`memory.db`) shared across all swarm inference cycles for context retention.
* **Autonomous WhatsApp Bridge**: Socket-level headless background messaging powered by Whiskeysockets Baileys daemon with dynamic contact lookup via `termux-contact-list`.
* **Tactical Cyberdeck HUD**: Dual-pane split-terminal interface powered by `tmux`, featuring a real-time system telemetry monitor (`hud_status.sh`) alongside an interactive agent REPL.
* **Autonomous ReAct Execution**: Self-correcting loop capable of running Bash shell utilities, isolated Python sandbox executions, and web-app hosting routines.
* **Integrated Recon & OSINT**: Built-in triggers for live DuckDuckGo web searches, Nmap port scanning, and automated network/VPN routing audits.
* **ChatGPT Spruce Voice Profile**: Hands-free voice synthesis output powered by Edge-TTS integration with configurable speech readouts (`-r` flag).

---

## 📁 Repository Architecture
```
Hyperoid-cli-agent/
├── install.sh                  # One-click deployment script
├── start_hud.sh                # Dual-pane tmux HUD initializer
├── hollywood_starship.toml     # Cyberpunk prompt configuration
├── README.md                   # System documentation
├── .gitignore                  # Excludes databases, logs, and caches
└── .hyperoid_agent/
    ├── auto_agent.py           # Core Level-9 ReAct orchestrator
    ├── hyperoid_listener.py    # Background wake-word listener ('Hyperoid')
    ├── skill_hub.py            # Dynamic skill compiler, web host & tunnel engine
    ├── duplex_voice.py         # Hands-free continuous voice loop
    ├── voice_ear.py            # Whisper voice ingestion utility
    ├── spruce_speaker.py       # Neural Spruce TTS synthesizer
    ├── sentinel_daemon.py      # Background battery & thermal watcher
    ├── web_deck.py             # Flask Web C2 control room
    ├── telegram_c2.py          # Remote Telegram C2 bot bridge
    └── hud_status.sh           # Left-pane cyberpunk interactive shell
```
---

## 🚀 Quick Installation

Run this single command inside Termux to clone and configure the entire system:
```bash

git clone https://github.com/suyogpawate-lab/Hyperoid-cli-agent.git
cd Hyperoid-cli-agent 
chmod +x install.sh start_hud.sh
bash install.sh
```
---

## ⚙️ Configuration

Configure your API keys in ~/.hyperoid_agent/config.json:
```bash
{
  "GROQ_API_KEY": "gsk_your_groq_api_key_here",
  "TELEGRAM_BOT_TOKEN": "",
  "TELEGRAM_ADMIN_ID": ""
}
```
---

## 🎮 Launching & Operational Modes

To start the HUD at any time:
```bash
hud

#(or execute ./start_hud.sh)

### Interactive Directives

# Spoken Readout Mode (-r):
  [AGENT_CMD] > -r Check battery status, active IP, and list all downloaded skills.

# Silent Mode:
  [AGENT_CMD] > Scan active subnet and ping 1.1.1.1

# Download & Learn New Skills:
  [AGENT_CMD] > Install the some_skill skill and tell me the main visual design rules.

# Host Web Apps & Open Public Tunnels:
  [AGENT_CMD] > Using some_skill rules, create a dark cyberpunk landing page, host it on port 5500, and open a public tunnel.
```
* Hands-Free Wake Word:
  Say "Hyperoid" aloud near your device. The system will chime, listen to your command, and vocalize the response.

---

## 🛠️ Requirements & Permissions

* Android 8.0+
* Termux (installed from F-Droid or GitHub Releases)
* Termux:API (installed and granted Location, Microphone, and SMS permissions)

---

HYPEROID Autonomous Systems // Online

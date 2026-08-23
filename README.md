# ⚡ HYPEROID // LEVEL-8 AUTONOMOUS CYBERDECK OS

<p align="center">
  <img src="https://img.shields.io/badge/PLATFORM-Android%2FTermux-00ffcc?style=for-the-badge&logo=android" />
  <img src="https://img.shields.io/badge/CORE-Autonomous%20ReAct%20Swarm-ff0055?style=for-the-badge" />
  <img src="https://img.shields.io/badge/VOICE-ChatGPT%20Spruce%20Neural-7cfc00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/INFERENCE-Groq%20LPU%20Ultra--Fast-blueviolet?style=for-the-badge" />
</p>

HYPEROID is an autonomous tactical cyberdeck operating system and AI agent terminal tailored specifically for Android / Termux. Designed with Hollywood cyberdeck telemetry aesthetics, it transforms an Android tablet or smartphone into a self-reflective, multi-agent AI command post.

---

## ⚡ Key Features

* Level-8 ReAct & Swarm Engine: Self-reflective Supervisor-Worker-Critic cycle that breaks down complex directives, executes tools in an isolated sandbox, reads outputs, inspects tracebacks, and self-corrects.
* ChatGPT Spruce Voice Profile: Natural, conversational neural speech synthesis powered by edge-tts (en-US-ChristopherNeural) with custom pacing and pitch tuning.
* Full-Duplex Interactive Voice Mode (duplex): Continuous, hands-free conversation loop powered by Groq's high-speed whisper-large-v3-turbo.
* Hardware-Level Android Control: Native hooks into battery telemetry, GPS coordinates, camera, screen brightness, SMS dispatch, flashlight, clipboard, and notifications via termux-api.
* Cyber Recon & Net Tools: Native integration with nmap, ping, active IP routing, and DuckDuckGo live web intelligence scraping.
* Document Ingestion RAG Vault: Automatic text, code, markdown, and PDF parsing into local SQLite storage with instant keyword/semantic retrieval.
* Web Cyberdeck Interface (http://127.0.0.1:8080): Lightweight neon web telemetry dashboard and control room accessible from any browser on your local network.
* Dual-Pane HUD (hud): Live telemetry system monitor on the left pane and the autonomous neural agent terminal on the right pane running inside tmux.

---

## 📁 Repository Architecture

Hyperoid-cli-agent/
├── install.sh                  # One-click deployment script
├── start_hud.sh                # Dual-pane tmux HUD initializer
├── hollywood_starship.toml     # Cyberpunk prompt configuration
├── README.md                   # System documentation
├── .gitignore                  # Excludes databases, logs, and caches
└── .hyperoid_agent/
    ├── auto_agent.py           # Core Level-8 ReAct orchestrator
    ├── duplex_voice.py         # Hands-free continuous voice loop
    ├── voice_ear.py            # Whisper voice ingestion utility
    ├── spruce_speaker.py       # Neural Spruce TTS synthesizer
    ├── sentinel_daemon.py      # Background battery & thermal watcher
    ├── web_deck.py             # Flask Web C2 control room
    ├── telegram_c2.py          # Remote Telegram C2 bot bridge
    └── hud_status.sh           # Left-pane live hardware visualizer

---

## 🚀 Quick Installation

Run this single command inside Termux to clone and configure the entire system:

pkg install -y git && \
git clone https://github.com/suyogpawate-lab/Hyperoid-cli-agent.git 
chmod +x install.sh start_hud.sh && \
./install.sh

---

## ⚙️ Configuration

Configure your API keys in ~/.hyperoid_agent/config.json:

{
  "GROQ_API_KEY": "gsk_your_groq_api_key_here",
  "TELEGRAM_BOT_TOKEN": "",
  "TELEGRAM_ADMIN_ID": ""
}

---

## 🎮 Launching & Operational Modes

To start the HUD at any time:

hud

(or execute ./start_hud.sh)

### Interactive Directives

* Standard Commands:
  [AGENT_CMD] > Check battery status, active IP, and save the result in vault under 'diagnostics'.

* Hands-Free Whisper Voice Mode:
  Type "voice" to record a single spoken command via whisper-large-v3-turbo.

* Full-Duplex Conversational Mode:
  Type "duplex" to enter continuous hands-free voice mode.

* Web C2 Control Room:
  Open http://localhost:8080 in your device browser for full remote control.

---

## 🛠️ Requirements & Permissions

* Android 8.0+
* Termux (installed from F-Droid or GitHub Releases)
* Termux:API (installed and granted Location, Microphone, and SMS permissions)

---

HYPEROID Autonomous Systems // Online

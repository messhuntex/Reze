# REZE — Android AI Voice Assistant
### *Personal Companion to Master Jit*

```
╔══════════════════════════════════════════════════════════════╗
║   Wake word: "Jit"  →  Reze activates  →  Voice command     ║
║   Futuristic · Female · Loyal · Teasing · Always Ready~      ║
╚══════════════════════════════════════════════════════════════╝
```

---

## What is Reze?

Reze is a **Jarvis-style AI voice assistant** that runs entirely on Android using Termux — **no root required**. She listens for the wake word **"Jit"**, understands your voice commands, replies in a female voice, controls your Android, and remembers things about you across sessions.

Powered by **Groq API** (ultra-fast LLaMA 70B), with offline fallback via Vosk.

---

## Project Structure

```
reze/
├── reze.py              ← Main entry point
├── setup.sh             ← One-click installer
├── .env.example         ← Config template
│
├── core/
│   ├── wake_word.py     ← Wake word detector ("Jit")
│   ├── speech.py        ← Voice → Text (Whisper/Vosk/Google)
│   ├── brain.py         ← Groq AI (LLaMA 70B) + personality
│   ├── tts.py           ← Text → Voice (female, termux-tts)
│   ├── commander.py     ← Android automation (Termux:API)
│   └── logger.py        ← Logging utility
│
├── memory/
│   └── memory.py        ← Persistent JSON memory system
│
└── models/
    └── vosk-model-small-en/  ← Offline STT model (auto-downloaded)
```

---

## Quick Start (5 Steps)

### Step 1 — Install Termux
Download **Termux** from **F-Droid** (NOT Play Store — Play Store version is outdated):
```
https://f-droid.org/en/packages/com.termux/
```

### Step 2 — Install Termux:API app
Download **Termux:API** from F-Droid for Android automation:
```
https://f-droid.org/en/packages/com.termux.api/
```
> In Android Settings → Apps → Termux:API → Permissions → enable all

### Step 3 — Get Groq API Key (FREE)
```
https://console.groq.com
```
Sign up → Create API Key → Copy it

### Step 4 — Run Setup
Open Termux and run:
```bash
# Clone the project
git clone https://github.com/YOUR_USERNAME/reze.git ~/reze
cd ~/reze

# Run setup (installs everything automatically)
bash setup.sh
```

### Step 5 — Add your API key
```bash
nano ~/reze/.env
# Change: GROQ_API_KEY=your_groq_api_key_here
# Press Ctrl+O to save, Ctrl+X to exit
```

### Launch Reze!
```bash
source ~/.bashrc
reze
```

---

## Voice Commands

After saying **"Jit"** to wake Reze:

| Command | What Reze Does |
|---|---|
| *"What's the time?"* | Tells current time |
| *"What's today's date?"* | Tells date |
| *"Battery status"* | Reports battery level |
| *"Open YouTube"* | Launches YouTube |
| *"Open WhatsApp"* | Launches WhatsApp |
| *"Flashlight on/off"* | Controls torch |
| *"Volume up/down"* | Adjusts media volume |
| *"Send message to John saying Hello"* | Sends SMS |
| *"Call Mom"* | Makes a phone call |
| *"My location"* | Gets GPS coordinates |
| *"Screenshot"* | Takes a screenshot |
| *"Remember I love coffee"* | Saves note to memory |
| *"What do you know about me?"* | Recalls saved notes |
| *"What can you do?"* | Lists capabilities |
| *"Stop"* / *"Goodbye"* | Reze goes to sleep |
| *Anything else* | Reze uses Groq AI to answer |

---

## Architecture Deep Dive

```
You say "Jit"
     │
     ▼
[Wake Word Detector]
 • Vosk offline model (primary — zero latency, no internet)
 • Google STT fallback (if Vosk unavailable)
     │
     ▼
[Speech Recognizer] — records ~7 seconds
 • Groq Whisper API (primary — most accurate)
 • Google STT (fallback)
 • Vosk offline (offline fallback)
     │
     ▼
[Android Commander] — checks for Android shortcuts first
 • Battery, time, date, wifi, torch, volume
 • Open apps, send SMS, call contacts
 • Location, screenshot, notifications
     │ (if not an Android command)
     ▼
[Reze Brain — Groq API]
 • Model: LLaMA 3.3 70B Versatile
 • Personality: Reze (female, teasing, loyal)
 • Context: conversation history + memory notes
 • Max tokens: 200 (optimized for voice)
     │
     ▼
[Memory System]
 • Auto-extracts facts from conversation
 • Persists JSON notes across sessions
 • Injects context into AI prompts
     │
     ▼
[Text-to-Speech]
 • termux-tts-speak (Android native — best)
 • espeak-ng (offline fallback)
 • pyttsx3 (last resort)
     │
     ▼
You hear Reze's response~
```

---

## Voice Quality — Getting the Best Female Voice

**Option A: Google TTS (Recommended)**
1. Android Settings → Accessibility → Text-to-speech output
2. Set "Preferred engine" to **Google Text-to-Speech**
3. Tap ⚙ → Install voice data → English (US)
4. Download a **female voice** (e.g., "English (US) - Voice 2")
5. Termux will automatically use this voice

**Option B: espeak-ng (offline)**
```bash
pkg install espeak
# Voice: en-us+f3 = female voice 3 (already configured in tts.py)
```

---

## Without Termux — Alternative Approaches

If you want a **full-screen experience** without Termux:

### Option 1: Kiwi Browser + Web App (Recommended for UI)
- Build Reze as a **Progressive Web App (PWA)**
- Use Web Speech API for STT/TTS (built into Chrome/Kiwi)
- Hosted locally via Python HTTP server in Termux
- Can run fullscreen from home screen

### Option 2: AIDE / Pydroid 3
- **Pydroid 3** (Play Store) runs Python with GUI support
- Can display a full-screen floating overlay
- Better for visual UI but no terminal

### Option 3: Tasker + Termux Integration
- **Tasker** (paid app) can trigger Termux scripts
- Create Tasker tasks that call Reze commands
- Add home screen widgets, automation triggers
- Can intercept physical buttons (volume, power) to trigger wake

### Option 4: Termux:Widget
```bash
pkg install termux-widget
# Creates home screen shortcuts that launch Reze
```

### Option 5: AutoVoice (Tasker plugin)
- Replace wake word detection with **AutoVoice** (Tasker plugin)
- Much more reliable wake word on Android
- Trigger Reze Python script via Tasker action

---

## Upgrading / Extending Reze

### Add a new voice command (example)
In `core/commander.py`, add to `try_handle()`:
```python
if re.search(r'alarm|wake me', text):
    return self._set_alarm(text)
```

### Add a new app shortcut
In the `APP_MAP` dict in `commander.py`:
```python
"netflix": "com.netflix.mediaclient",
"tiktok":  "com.zhiliaoapp.musically",
```

### Change Reze's personality
Edit `SYSTEM_PROMPT` in `core/brain.py`.

### Change wake word
In `.env`:
```
WAKE_WORD=hello
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "termux-tts-speak not found" | Install Termux:API from F-Droid |
| "GROQ_API_KEY not set" | Run `nano ~/reze/.env` and add key |
| No microphone access | Termux Settings → Microphone permission |
| Vosk model missing | Run `bash setup.sh` again |
| Wake word not detecting | Increase mic sensitivity, speak clearly |
| SMS not sending | Grant SMS permission to Termux:API |

---

## Requirements Summary

| Requirement | Solution |
|---|---|
| Android only | ✅ Termux + Termux:API |
| No root | ✅ All via Termux:API |
| Wake word | ✅ Vosk offline keyword spotter |
| Voice input | ✅ Groq Whisper + Google STT |
| AI responses | ✅ Groq LLaMA 3.3 70B |
| Female voice | ✅ termux-tts-speak (Google TTS female voice) |
| Persistent memory | ✅ JSON-based memory system |
| Android automation | ✅ Termux:API commands |
| Low latency | ✅ Groq ~100ms response time |
| Offline fallback | ✅ Vosk STT + espeak TTS |

---

*"Systems online, Master Jit. Reze reporting for duty~"*

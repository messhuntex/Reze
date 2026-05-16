#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  REZE — One-Shot Setup Script for Termux (Android, no root)
#  Run once after cloning the project
# ============================================================

set -e

REZE_DIR="$HOME/reze"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

banner() {
cat << 'EOF'
╔══════════════════════════════════════════════╗
║   R E Z E  —  AI Assistant Setup            ║
║   Personal Assistant to Master Jit           ║
╚══════════════════════════════════════════════╝
EOF
}

step() { echo -e "\n${CYAN}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✔ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
err()  { echo -e "${RED}✘ $1${NC}"; }

banner

# ── 1. Update Termux packages ─────────────────────────────────
step "Updating Termux packages…"
pkg update -y && pkg upgrade -y
ok "Packages updated"

# ── 2. Install system dependencies ───────────────────────────
step "Installing system dependencies…"
pkg install -y \
    python \
    python-pip \
    ffmpeg \
    espeak \
    wget \
    curl \
    git \
    termux-api
ok "System deps installed"

# ── 3. Storage permission ─────────────────────────────────────
step "Requesting storage permission…"
termux-setup-storage || warn "Grant storage permission manually in Android Settings"

# ── 4. Create project directories ────────────────────────────
step "Creating directories…"
mkdir -p "$REZE_DIR"/{tmp,memory,logs,models}
ok "Directories ready"

# ── 5. Install Python packages ────────────────────────────────
step "Installing Python packages (no build-dependencies)…"

# Core packages — all pure Python or pre-built wheels for Android
pip install --upgrade pip

pip install \
    requests \
    python-dotenv \
    SpeechRecognition

ok "Core Python packages installed"

# Optional: Vosk (offline wake word + STT)
step "Installing Vosk (offline STT — recommended)…"
pip install vosk && ok "Vosk installed" || warn "Vosk install failed — will use online STT"

# ── 6. Download Vosk small English model ─────────────────────
VOSK_MODEL="$REZE_DIR/models/vosk-model-small-en"
if [ ! -d "$VOSK_MODEL" ]; then
    step "Downloading Vosk small English model (~40MB)…"
    MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    wget -q --show-progress -O /tmp/vosk-model.zip "$MODEL_URL" && \
    unzip -q /tmp/vosk-model.zip -d "$REZE_DIR/models/" && \
    mv "$REZE_DIR/models/vosk-model-small-en-us-0.15" "$VOSK_MODEL" && \
    rm /tmp/vosk-model.zip && \
    ok "Vosk model downloaded" || \
    warn "Vosk model download failed — add manually later"
else
    ok "Vosk model already present"
fi

# ── 7. .env setup ─────────────────────────────────────────────
step "Setting up .env config…"
if [ ! -f "$REZE_DIR/.env" ]; then
    cp "$REZE_DIR/.env.example" "$REZE_DIR/.env"
    echo ""
    echo -e "${BOLD}${YELLOW}ACTION REQUIRED:${NC}"
    echo -e "Edit your API key in: ${CYAN}$REZE_DIR/.env${NC}"
    echo -e "Get a free Groq key at: ${CYAN}https://console.groq.com${NC}"
    echo -e "Run: ${CYAN}nano $REZE_DIR/.env${NC}"
else
    ok ".env already exists"
fi

# ── 8. Make reze.py executable ────────────────────────────────
chmod +x "$REZE_DIR/reze.py"

# ── 9. Create quick-launch alias ─────────────────────────────
step "Adding 'reze' command alias…"
BASHRC="$HOME/.bashrc"
if ! grep -q "alias reze=" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# Reze AI Assistant" >> "$BASHRC"
    echo "alias reze='cd $REZE_DIR && python reze.py'" >> "$BASHRC"
    echo "export PYTHONPATH=$REZE_DIR:\$PYTHONPATH" >> "$BASHRC"
    ok "Alias 'reze' added to .bashrc"
else
    ok "Alias already exists"
fi

# ── 10. TTS voice check ───────────────────────────────────────
step "Testing TTS (text-to-speech)…"
termux-tts-speak "Reze setup complete. Hello Master Jit." 2>/dev/null && \
    ok "TTS working via Termux API" || \
    warn "termux-tts-speak not available — install Termux:API app from F-Droid"

# ── Done ─────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  Setup Complete! Reze is ready.              ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. ${CYAN}nano $REZE_DIR/.env${NC}  — add your GROQ_API_KEY"
echo -e "  2. ${CYAN}source ~/.bashrc${NC}    — reload shell"
echo -e "  3. ${CYAN}reze${NC}                — launch Reze!"
echo -e "  4. Say ${BOLD}'Jit'${NC} to wake her up~"
echo ""
echo -e "Optional (better voice):"
echo -e "  • Install ${CYAN}Termux:API${NC} app from F-Droid"
echo -e "  • In Android Settings → Accessibility → TTS → set Google TTS"
echo -e "  • Choose a female English voice in TTS settings"
echo ""


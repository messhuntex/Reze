#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           R E Z E  —  AI Voice Assistant                     ║
║           Personal Assistant to Master Jit                   ║
║           Built for Android / Termux (No Root)               ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import threading
import signal
import subprocess
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from core.wake_word     import WakeWordDetector
from core.speech        import SpeechRecognizer
from core.brain         import RezeBrain
from core.tts           import TextToSpeech
from core.commander     import AndroidCommander
from memory.memory      import RezeMemory
from core.logger        import log


# ─── Config ────────────────────────────────────────────────────
WAKE_WORD   = "jit"          # Say "Jit" to activate Reze
MASTER_NAME = "Master Jit"
REZE_NAME   = "Reze"


class RezeAssistant:
    """Core orchestrator — wake → listen → think → speak → act."""

    def __init__(self):
        log.info("Initializing Reze …")
        self.memory    = RezeMemory()
        self.brain     = RezeBrain(self.memory)
        self.tts       = TextToSpeech()
        self.stt       = SpeechRecognizer()
        self.wake      = WakeWordDetector(wake_word=WAKE_WORD, callback=self._on_wake)
        self.commander = AndroidCommander()
        self._running  = True
        signal.signal(signal.SIGINT,  self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    # ─── Boot greeting ──────────────────────────────────────────
    def start(self):
        greeting = (
            f"Systems online, {MASTER_NAME}. "
            "I am Reze, your personal AI companion. "
            "Say 'Jit' whenever you need me. "
            "I'll be right here… watching~"
        )
        log.info("Reze online.")
        self.tts.speak(greeting)
        self.wake.start()

        # Keep main thread alive
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._shutdown()

    # ─── Wake word callback ─────────────────────────────────────
    def _on_wake(self):
        self.tts.speak("Yes, Master Jit?")
        log.info("Wake word detected — listening …")
        command = self.stt.listen()
        if command:
            self._handle(command)
        else:
            self.tts.speak("I didn't catch that. Try again~")

    # ─── Main command handler ───────────────────────────────────
    def _handle(self, text: str):
        text_lower = text.lower().strip()
        log.info(f"Command: {text}")

        # ── Built-in shortcuts ───────────────────────────────────
        if any(k in text_lower for k in ["stop", "goodbye", "shutdown", "sleep"]):
            self.tts.speak(f"Understood, {MASTER_NAME}. Going to sleep. Miss me~")
            self.wake.stop()
            self._running = False
            return

        if "what can you do" in text_lower or "help" in text_lower:
            self._say_help()
            return

        if "remember" in text_lower:
            self._handle_memory_save(text)
            return

        if "recall" in text_lower or "what do you know" in text_lower:
            self._handle_memory_recall(text)
            return

        # ── Android automation shortcuts ─────────────────────────
        android_response = self.commander.try_handle(text_lower)
        if android_response:
            self.tts.speak(android_response)
            return

        # ── AI Brain (Groq) ──────────────────────────────────────
        response = self.brain.chat(text)
        self.tts.speak(response)

    # ─── Memory helpers ─────────────────────────────────────────
    def _handle_memory_save(self, text: str):
        # e.g. "remember my favorite color is red"
        clean = text.lower().replace("remember", "").replace("that", "").strip()
        self.memory.save("user_note", clean)
        self.tts.speak(f"Noted, {MASTER_NAME}. I'll never forget that~")

    def _handle_memory_recall(self, text: str):
        notes = self.memory.get_all_notes()
        if notes:
            joined = ". ".join(notes[-5:])
            self.tts.speak(f"Here's what I remember about you: {joined}")
        else:
            self.tts.speak(f"I don't have any special notes yet, {MASTER_NAME}.")

    def _say_help(self):
        help_text = (
            f"I can do quite a lot for you, {MASTER_NAME}. "
            "Ask me anything — questions, calculations, creative writing. "
            "Say 'open app' followed by the app name to launch apps. "
            "Say 'send message' to compose texts. "
            "Say 'remember' followed by anything to store a note. "
            "Say 'recall' to hear your saved notes. "
            "Say 'time' or 'date' for current time. "
            "And of course… I'm always here just to talk~"
        )
        self.tts.speak(help_text)

    # ─── Graceful shutdown ───────────────────────────────────────
    def _shutdown(self, *_):
        log.info("Shutting down Reze …")
        self.wake.stop()
        self._running = False
        sys.exit(0)


# ─── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    assistant = RezeAssistant()
    assistant.start()
  

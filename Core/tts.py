"""
tts.py — Text-to-Speech for Reze
Priority:
  1. termux-tts-speak (Android native, best integration)
  2. espeak-ng (offline, works in Termux)
  3. pyttsx3 (fallback)
"""

import subprocess
import threading
import os
from core.logger import log


class TextToSpeech:

    def __init__(self):
        self.engine  = self._detect_engine()
        self._lock   = threading.Lock()
        log.info(f"TTS engine: {self.engine}")

        # Voice settings
        self.rate   = 145   # words per minute (slightly faster = more energy)
        self.pitch  = 65    # higher pitch = more feminine (termux-tts-speak scale)

    # ─── Public API ─────────────────────────────────────────────
    def speak(self, text: str, block: bool = True):
        """Speak text. If block=False, runs in background thread."""
        if not text:
            return
        text = self._clean(text)
        log.info(f"Reze speaks: {text[:60]}…" if len(text) > 60 else f"Reze speaks: {text}")

        if block:
            self._speak_now(text)
        else:
            threading.Thread(target=self._speak_now, args=(text,), daemon=True).start()

    # ─── Engine detection ────────────────────────────────────────
    def _detect_engine(self) -> str:
        """Auto-detect the best available TTS engine."""
        if self._cmd_exists("termux-tts-speak"):
            return "termux"
        if self._cmd_exists("espeak-ng") or self._cmd_exists("espeak"):
            return "espeak"
        try:
            import pyttsx3
            return "pyttsx3"
        except ImportError:
            pass
        return "print"  # last resort — just print

    @staticmethod
    def _cmd_exists(cmd: str) -> bool:
        result = subprocess.run(["which", cmd], capture_output=True)
        return result.returncode == 0

    # ─── Speak implementations ───────────────────────────────────
    def _speak_now(self, text: str):
        with self._lock:
            if self.engine == "termux":
                self._speak_termux(text)
            elif self.engine == "espeak":
                self._speak_espeak(text)
            elif self.engine == "pyttsx3":
                self._speak_pyttsx3(text)
            else:
                print(f"\n🎙  Reze: {text}\n")

    def _speak_termux(self, text: str):
        """
        termux-tts-speak: uses Android's built-in TTS engine.
        Install voices: Settings → Accessibility → TTS → Add language.
        Recommended voice: Google TTS → English (US) → female voice
        """
        try:
            subprocess.run(
                ["termux-tts-speak",
                 "-r", str(self.rate),
                 "-p", str(self.pitch),
                 text],
                timeout=60, check=True
            )
        except subprocess.TimeoutExpired:
            log.warning("TTS timeout")
        except Exception as e:
            log.error(f"termux-tts-speak error: {e}")
            self._speak_espeak(text)  # fallback

    def _speak_espeak(self, text: str):
        """
        espeak-ng: offline TTS.
        pkg install espeak
        Female voice: -v en-us+f3
        """
        try:
            cmd = "espeak-ng" if self._cmd_exists("espeak-ng") else "espeak"
            subprocess.run(
                [cmd, "-v", "en-us+f3",
                 "-s", str(self.rate),
                 "-p", str(self.pitch),
                 text],
                timeout=60
            )
        except Exception as e:
            log.error(f"espeak error: {e}")
            print(f"\n🎙  Reze: {text}\n")

    def _speak_pyttsx3(self, text: str):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            # Try to select a female voice
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate",  self.rate)
            engine.setProperty("volume", 1.0)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            log.error(f"pyttsx3 error: {e}")
            print(f"\n🎙  Reze: {text}\n")

    # ─── Text cleanup ────────────────────────────────────────────
    @staticmethod
    def _clean(text: str) -> str:
        """Remove markdown and symbols that sound bad when spoken."""
        import re
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'`+', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = text.replace("~", "").replace("•", "").strip()
        return text

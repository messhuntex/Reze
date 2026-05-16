"""
wake_word.py — Lightweight wake-word detection for Termux (no root)
Uses SpeechRecognition with continuous looped listening.
No heavy offline engine needed; works with Android mic via Termux:API.
"""

import threading
import time
import subprocess
import json
from core.logger import log


class WakeWordDetector:
    """
    Polls the microphone in a background thread.
    When the wake word is heard, fires `callback()`.

    Strategy (Termux-compatible, no root):
      1. Use termux-microphone-record to capture short audio clips
      2. Transcribe via Vosk (offline) or Whisper (via Groq)
      3. Check for wake word in transcript
    """

    def __init__(self, wake_word: str = "jit", callback=None, interval: float = 1.5):
        self.wake_word  = wake_word.lower()
        self.callback   = callback
        self.interval   = interval
        self._running   = False
        self._thread    = None
        self._locked    = False   # prevent re-trigger during active session

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        log.info(f"Wake word detector started — listening for '{self.wake_word}'")

    def stop(self):
        self._running = False
        log.info("Wake word detector stopped.")

    def unlock(self):
        """Call after a command session ends so listening resumes."""
        self._locked = False

    # ─── Internal loop ───────────────────────────────────────────
    def _loop(self):
        while self._running:
            if self._locked:
                time.sleep(0.3)
                continue
            try:
                text = self._capture_snippet()
                if text and self.wake_word in text.lower():
                    log.info(f"Wake word '{self.wake_word}' detected!")
                    self._locked = True
                    if self.callback:
                        self.callback()
                    self._locked = False
            except Exception as e:
                log.warning(f"Wake word loop error: {e}")
            time.sleep(self.interval)

    # ─── Audio capture via Termux:API ────────────────────────────
    def _capture_snippet(self) -> str:
        """
        Record 2-second audio clip and transcribe it.
        Falls back to Vosk offline STT for zero-latency.
        """
        try:
            # Record audio to temp WAV using termux-microphone-record
            audio_file = "/data/data/com.termux/files/home/reze/tmp/wake_snippet.mp4"
            rec_cmd = [
                "termux-microphone-record",
                "-l", "2",          # 2-second limit
                "-e", "aac",
                "-f", audio_file
            ]
            subprocess.run(rec_cmd, timeout=3, capture_output=True)
            time.sleep(2.2)  # wait for recording to finish

            # Transcribe with Vosk (offline, fast)
            return self._vosk_transcribe(audio_file)

        except FileNotFoundError:
            # Termux:API not installed — fall back to SpeechRecognition
            return self._sr_fallback()
        except Exception as e:
            log.debug(f"Capture error: {e}")
            return ""

    def _vosk_transcribe(self, audio_file: str) -> str:
        """Use Vosk small model for offline keyword detection."""
        try:
            import vosk
            import wave
            import json as _json

            model_path = "/data/data/com.termux/files/home/reze/models/vosk-model-small-en"
            if not __import__("os").path.exists(model_path):
                log.warning("Vosk model not found. Run setup.sh to download it.")
                return ""

            model = vosk.Model(model_path)
            wf    = wave.open(audio_file, "rb")
            rec   = vosk.KaldiRecognizer(model, wf.getframerate())

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

            result = _json.loads(rec.FinalResult())
            return result.get("text", "")
        except Exception as e:
            log.debug(f"Vosk error: {e}")
            return ""

    def _sr_fallback(self) -> str:
        """
        Fallback: use SpeechRecognition with Google online STT
        (requires internet — used only when Vosk is unavailable).
        """
        try:
            import speech_recognition as sr
            r   = sr.Recognizer()
            r.energy_threshold        = 300
            r.dynamic_energy_threshold = True
            mic = sr.Microphone()
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=2, phrase_time_limit=2)
            return r.recognize_google(audio)
        except Exception:
            return ""

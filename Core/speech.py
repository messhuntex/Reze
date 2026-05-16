"""
speech.py — Speech-to-Text for Reze (Termux, no root)
Primary : Groq Whisper API  (fast, accurate, cloud)
Fallback : SpeechRecognition + Google STT (online)
Offline  : Vosk small model (when no internet)
"""

import os
import subprocess
import time
import json
import tempfile
from core.logger import log


class SpeechRecognizer:

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.tmp_dir      = "/data/data/com.termux/files/home/reze/tmp"
        os.makedirs(self.tmp_dir, exist_ok=True)

    # ─── Public API ─────────────────────────────────────────────
    def listen(self, timeout: int = 7) -> str:
        """Record audio and return transcribed text."""
        audio_path = self._record(timeout)
        if not audio_path:
            return ""
        text = self._transcribe(audio_path)
        log.info(f"STT result: {text!r}")
        return text

    # ─── Recording ───────────────────────────────────────────────
    def _record(self, duration: int) -> str:
        """Record audio via Termux:API mic."""
        out = f"{self.tmp_dir}/command.wav"
        try:
            # Termux:API approach
            subprocess.run(
                ["termux-microphone-record", "-l", str(duration), "-f", out],
                timeout=duration + 2, capture_output=True, check=True
            )
            time.sleep(duration + 0.5)
            return out
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        # Fallback: arecord (may need audio group perms)
        try:
            subprocess.run(
                ["arecord", "-d", str(duration), "-r", "16000",
                 "-f", "S16_LE", "-t", "wav", out],
                timeout=duration + 2, capture_output=True, check=True
            )
            return out
        except Exception as e:
            log.error(f"Recording failed: {e}")
            return ""

    # ─── Transcription ───────────────────────────────────────────
    def _transcribe(self, audio_path: str) -> str:
        """Try Groq Whisper → Google STT → Vosk."""

        # 1) Groq Whisper (best quality, fast)
        if self.groq_api_key:
            result = self._groq_whisper(audio_path)
            if result:
                return result

        # 2) SpeechRecognition + Google
        result = self._google_stt(audio_path)
        if result:
            return result

        # 3) Vosk offline
        return self._vosk_stt(audio_path)

    def _groq_whisper(self, path: str) -> str:
        try:
            import requests
            with open(path, "rb") as f:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.groq_api_key}"},
                    files={"file": ("audio.wav", f, "audio/wav")},
                    data={"model": "whisper-large-v3-turbo", "language": "en"},
                    timeout=10
                )
            if resp.ok:
                return resp.json().get("text", "").strip()
        except Exception as e:
            log.warning(f"Groq Whisper error: {e}")
        return ""

    def _google_stt(self, path: str) -> str:
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(path) as source:
                audio = r.record(source)
            return r.recognize_google(audio)
        except Exception as e:
            log.debug(f"Google STT error: {e}")
        return ""

    def _vosk_stt(self, path: str) -> str:
        try:
            import vosk, wave, json as _j
            model_path = "/data/data/com.termux/files/home/reze/models/vosk-model-small-en"
            if not os.path.exists(model_path):
                return ""
            model = vosk.Model(model_path)
            wf    = wave.open(path, "rb")
            rec   = vosk.KaldiRecognizer(model, wf.getframerate())
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                rec.AcceptWaveform(data)
            return _j.loads(rec.FinalResult()).get("text", "")
        except Exception as e:
            log.debug(f"Vosk STT error: {e}")
        return ""

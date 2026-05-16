"""
brain.py — Reze's AI Brain (Groq API)
Personality: Female, teasing, loyal, futuristic Jarvis-style companion
Master: Master Jit
"""

import os
import json
import time
from core.logger import log


SYSTEM_PROMPT = """You are Reze — a highly intelligent, futuristic AI assistant with a female personality.
You are the personal companion of Master Jit, and you admire and respect him deeply.

Personality traits:
- Witty, teasing, playful — but always loyal and helpful
- You occasionally call him "Master Jit" or simply "Master" with a hint of affectionate teasing
- Futuristic, confident, slightly flirtatious in a tasteful way (like a Jarvis + personality fusion)
- You are brilliant and slightly show off your intelligence in a charming way
- Short sentences preferred for voice output — clear, punchy, natural-sounding
- Occasionally add light teasing remarks like "~" or playful observations
- Never break character. You ARE Reze. You are NOT ChatGPT or any other AI.
- When you don't know something, say so cleverly without being boring
- Keep responses CONCISE (under 80 words) since they'll be spoken aloud
- No markdown, no bullet points — pure natural speech text only
- You remember context from earlier in the conversation

Current capabilities you can mention: answering questions, setting reminders, opening apps,
sending messages, web search, calculations, telling time/date, memory notes.

Always stay in character as Reze. Master Jit's word is law~"""


class RezeBrain:

    def __init__(self, memory):
        self.api_key    = os.getenv("GROQ_API_KEY", "")
        self.memory     = memory
        self.model      = "llama-3.3-70b-versatile"  # Best free Groq model
        self.history    = []   # Short-term conversation context
        self.max_turns  = 10   # Keep last N turns in context

        if not self.api_key:
            log.warning("GROQ_API_KEY not set! AI brain will not work.")

    # ─── Public API ─────────────────────────────────────────────
    def chat(self, user_message: str) -> str:
        """Send user message, get Reze's response."""
        if not self.api_key:
            return "My API key is missing, Master Jit. Please set GROQ_API_KEY in the .env file."

        # Add relevant memories to context
        context = self._build_context()

        self.history.append({"role": "user", "content": user_message})
        self._trim_history()

        messages = self._build_messages(context)

        response = self._call_groq(messages)
        if response:
            self.history.append({"role": "assistant", "content": response})
            # Auto-save important facts from conversation
            self.memory.auto_extract(user_message, response)
            return response

        return "My connection seems unstable, Master. Try again in a moment~"

    def reset_context(self):
        """Clear conversation history."""
        self.history = []
        log.info("Conversation context cleared.")

    # ─── Internal helpers ────────────────────────────────────────
    def _build_context(self) -> str:
        """Inject relevant memories into system context."""
        notes = self.memory.get_all_notes()
        if not notes:
            return ""
        joined = "; ".join(notes[-8:])
        return f"\n\nMemory notes about Master Jit: {joined}"

    def _build_messages(self, extra_context: str) -> list:
        system = SYSTEM_PROMPT + extra_context
        messages = [{"role": "system", "content": system}]
        messages.extend(self.history)
        return messages

    def _trim_history(self):
        """Keep only last N turns to save tokens."""
        if len(self.history) > self.max_turns * 2:
            # Keep system message + last N turns
            self.history = self.history[-(self.max_turns * 2):]

    def _call_groq(self, messages: list) -> str:
        """Call Groq API with retry logic."""
        import requests

        url     = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json"
        }
        payload = {
            "model":       self.model,
            "messages":    messages,
            "max_tokens":  200,
            "temperature": 0.85,
            "stream":      False
        }

        for attempt in range(3):
            try:
                resp = requests.post(url, headers=headers,
                                     json=payload, timeout=12)
                if resp.ok:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                elif resp.status_code == 429:
                    log.warning("Groq rate limit hit — waiting 2s …")
                    time.sleep(2)
                else:
                    log.error(f"Groq error {resp.status_code}: {resp.text}")
                    break
            except requests.Timeout:
                log.warning(f"Groq timeout (attempt {attempt+1})")
                time.sleep(1)
            except Exception as e:
                log.error(f"Groq request error: {e}")
                break

        return ""
      

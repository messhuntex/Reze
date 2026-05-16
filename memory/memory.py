"""
memory.py — Persistent Memory System for Reze
Stores facts about Master Jit and conversation context.
Uses simple JSON files — no external DB needed.
"""

import os
import json
import time
import re
from pathlib import Path
from core.logger import log


MEMORY_DIR  = Path("/data/data/com.termux/files/home/reze/memory")
NOTES_FILE  = MEMORY_DIR / "notes.json"
FACTS_FILE  = MEMORY_DIR / "facts.json"
HISTORY_FILE = MEMORY_DIR / "history.json"


class RezeMemory:

    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.notes   = self._load(NOTES_FILE, [])
        self.facts   = self._load(FACTS_FILE, {})
        self.history = self._load(HISTORY_FILE, [])
        log.info(f"Memory loaded: {len(self.notes)} notes, {len(self.facts)} facts.")

    # ─── Notes (manual saves) ────────────────────────────────────
    def save(self, key: str, value: str):
        entry = {
            "key":   key,
            "value": value,
            "time":  time.strftime("%Y-%m-%d %H:%M")
        }
        self.notes.append(entry)
        self._save(NOTES_FILE, self.notes)
        log.info(f"Memory saved: {key} = {value}")

    def get_all_notes(self) -> list[str]:
        return [n["value"] for n in self.notes]

    def search_notes(self, query: str) -> list[str]:
        q = query.lower()
        return [n["value"] for n in self.notes if q in n["value"].lower()]

    def forget_all(self):
        self.notes = []
        self.facts = {}
        self._save(NOTES_FILE, self.notes)
        self._save(FACTS_FILE, self.facts)
        log.info("Memory cleared.")

    # ─── Structured facts ────────────────────────────────────────
    def set_fact(self, key: str, value: str):
        self.facts[key] = value
        self._save(FACTS_FILE, self.facts)

    def get_fact(self, key: str, default="") -> str:
        return self.facts.get(key, default)

    # ─── Conversation history (long-term) ────────────────────────
    def append_history(self, role: str, content: str):
        self.history.append({
            "role":    role,
            "content": content,
            "time":    time.strftime("%Y-%m-%d %H:%M")
        })
        # Keep only last 200 entries
        if len(self.history) > 200:
            self.history = self.history[-200:]
        self._save(HISTORY_FILE, self.history)

    def get_recent_history(self, n: int = 10) -> list[dict]:
        return self.history[-n:]

    # ─── Auto-extraction from conversation ───────────────────────
    def auto_extract(self, user_msg: str, bot_msg: str):
        """
        Automatically extract and store facts from conversation.
        E.g. "My name is Jit" → stores {name: Jit}
        """
        patterns = [
            (r"my name is (\w+)",         "master_name"),
            (r"i(?:'m| am) (\d+) years",  "master_age"),
            (r"i live in ([\w\s]+)",       "master_city"),
            (r"i work (?:at|for) ([\w\s]+)", "master_workplace"),
            (r"i like ([\w\s]+)",          "master_likes"),
            (r"i love ([\w\s]+)",          "master_loves"),
            (r"my (?:phone )?number is ([\d\s+\-]+)", "master_phone"),
        ]
        text = user_msg.lower()
        for pattern, fact_key in patterns:
            m = re.search(pattern, text)
            if m:
                value = m.group(1).strip()
                self.set_fact(fact_key, value)
                log.info(f"Auto-extracted fact: {fact_key} = {value}")

    # ─── Summary for context injection ───────────────────────────
    def get_context_summary(self) -> str:
        """Returns a compact summary for injecting into AI system prompt."""
        parts = []
        for k, v in self.facts.items():
            parts.append(f"{k.replace('_', ' ')}: {v}")
        recent = [n["value"] for n in self.notes[-5:]]
        if recent:
            parts.extend(recent)
        return "; ".join(parts)

    # ─── File helpers ────────────────────────────────────────────
    @staticmethod
    def _load(path: Path, default):
        try:
            if path.exists():
                with open(path, "r") as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"Memory load error ({path.name}): {e}")
        return default

    @staticmethod
    def _save(path: Path, data):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"Memory save error ({path.name}): {e}")

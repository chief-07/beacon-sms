"""
Memory Service: In-memory session tracking for SMS conversation history with TTL.
Enables multi-turn context on dumb feature phones.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class UserSession:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.history: List[Dict[str, str]] = []  # [{"role": "user"/"assistant", "content": "..."}]
        self.last_active = datetime.now(timezone.utc)

    def add_message(self, role: str, content: str, max_turns: int = 3):
        self.history.append({"role": role, "content": content})
        self.last_active = datetime.now(timezone.utc)
        # Keep only the last N turns (1 turn = 1 user + 1 assistant)
        max_messages = max_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def get_messages(self) -> List[Dict[str, str]]:
        return self.history


class MemoryService:
    def __init__(self, ttl_minutes: int = 20, max_turns: int = 3):
        self.sessions: Dict[str, UserSession] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_turns = max_turns

    def _cleanup(self):
        """Remove expired sessions to prevent memory leaks."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            phone for phone, session in self.sessions.items()
            if now - session.last_active > self.ttl
        ]
        for key in expired_keys:
            del self.sessions[key]

    def get_or_create_session(self, phone_number: str) -> UserSession:
        self._cleanup()
        clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
        if clean_phone not in self.sessions:
            self.sessions[clean_phone] = UserSession(clean_phone)
        return self.sessions[clean_phone]

    def add_user_message(self, phone_number: str, content: str):
        session = self.get_or_create_session(phone_number)
        session.add_message("user", content, max_turns=self.max_turns)

    def add_assistant_message(self, phone_number: str, content: str):
        session = self.get_or_create_session(phone_number)
        session.add_message("assistant", content, max_turns=self.max_turns)

    def get_conversation_history(self, phone_number: str) -> List[Dict[str, str]]:
        self._cleanup()
        clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
        if clean_phone in self.sessions:
            return self.sessions[clean_phone].get_messages()
        return []

    def clear_session(self, phone_number: str):
        clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
        if clean_phone in self.sessions:
            del self.sessions[clean_phone]


# Singleton instance
memory_service = MemoryService()

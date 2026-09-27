"""
AI Service: Lightweight Multilingual Intelligence engine.
Uses direct REST HTTP calls for Google Gemini (fastest, zero heavy SDK overhead).
Applies SMS-safe text cleaning and character budgeting.
"""

import re
import unicodedata
import logging
import httpx
from typing import List, Dict, Optional

from src.config import settings
from src.prompts.system_prompts import build_system_prompt
from src.services.memory_service import memory_service

logger = logging.getLogger(__name__)


def sanitize_for_sms(text: str, max_chars: int = 280) -> str:
    """
    Cleans text for SMS transmission:
    1. Removes Markdown symbols (*, #, `, _, ~)
    2. Converts accented characters to plain ASCII to protect GSM-7 160-char encoding
    3. Normalizes whitespace and newlines
    4. Truncates cleanly if exceeding character budget
    """
    if not text:
        return ""

    # Strip markdown syntax
    clean = re.sub(r'[*#_~`>]', '', text)
    clean = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean)  # Replace [link](url) with just link

    # Normalize unicode to ASCII where possible (e.g. é -> e, tone marks removed)
    # This prevents carriers from forcing UCS-2 (which cuts SMS limit to 70 chars)
    normalized = unicodedata.normalize('NFKD', clean)
    ascii_clean = normalized.encode('ASCII', 'ignore').decode('ASCII')

    # Normalize excessive newlines/spaces
    ascii_clean = re.sub(r'\n{3,}', '\n\n', ascii_clean).strip()

    # Truncate cleanly at word boundary if over max_chars
    if len(ascii_clean) > max_chars:
        truncated = ascii_clean[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > max_chars - 30:
            ascii_clean = truncated[:last_space] + "..."
        else:
            ascii_clean = truncated + "..."

    return ascii_clean


class AIService:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self._init_clients()

    def _init_clients(self):
        # Groq client initialization (if configured)
        self.groq_client = None
        if settings.groq_api_key:
            try:
                from groq import AsyncGroq
                self.groq_client = AsyncGroq(api_key=settings.groq_api_key)
                logger.info(f"Groq client initialized with model: {settings.groq_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")

        # OpenAI client initialization (if configured)
        self.openai_client = None
        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info(f"OpenAI client initialized with model: {settings.openai_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

    async def generate_response(self, phone_number: str, user_message: str) -> str:
        """
        Generate localized AI response using conversation history and character budgeting.
        """
        history = memory_service.get_conversation_history(phone_number)
        system_prompt = build_system_prompt(settings.max_sms_characters)

        response_text = ""

        try:
            if self.provider == "gemini" and settings.gemini_api_key:
                response_text = await self._generate_gemini_rest(system_prompt, history, user_message)
            elif self.provider == "groq" and self.groq_client:
                response_text = await self._generate_groq(system_prompt, history, user_message)
            elif self.provider == "openai" and self.openai_client:
                response_text = await self._generate_openai(system_prompt, history, user_message)
            else:
                # Automatic fallback cascade
                if settings.gemini_api_key:
                    response_text = await self._generate_gemini_rest(system_prompt, history, user_message)
                elif self.groq_client:
                    response_text = await self._generate_groq(system_prompt, history, user_message)
                elif self.openai_client:
                    response_text = await self._generate_openai(system_prompt, history, user_message)
                else:
                    return "Beacon Alert: System is temporarily offline. Please verify API key configuration."

        except Exception as e:
            logger.error(f"Error generating AI response via {self.provider}: {e}")
            return "Beacon: Network delay in processing your request. Please try again shortly or seek immediate local help."

        # Sanitize and fit into SMS character budget
        clean_response = sanitize_for_sms(response_text, settings.max_sms_characters)

        # Update conversational memory
        memory_service.add_user_message(phone_number, user_message)
        memory_service.add_assistant_message(phone_number, clean_response)

        return clean_response

    async def _generate_gemini_rest(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> str:
        """
        Calls Google Gemini directly via lightweight HTTP REST.
        Ultra-fast, zero heavy SDK overhead, and 100% compatible with modern 'AQ.' auth keys.
        """
        model = settings.gemini_model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}"

        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 800,
                "temperature": 0.2
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Gemini REST error {resp.status_code}: {resp.text}")
                resp.raise_for_status()

            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                if text_parts:
                    return "".join(text_parts).strip()

            return ""

    async def _generate_groq(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        completion = await self.groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            max_tokens=150,
            temperature=0.3
        )
        return completion.choices[0].message.content or ""

    async def _generate_openai(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        completion = await self.openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=150,
            temperature=0.3
        )
        return completion.choices[0].message.content or ""


# Singleton instance
ai_service = AIService()

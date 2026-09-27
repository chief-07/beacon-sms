"""
AI Service: Multilingual Intelligence engine supporting Google Gemini, Groq, and OpenAI.
Applies SMS-safe text cleaning and character budgeting.
"""

import re
import unicodedata
import logging
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
        # Gemini initialization
        self.gemini_model = None
        if settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name=settings.gemini_model,
                    system_instruction=build_system_prompt(settings.max_sms_characters)
                )
                logger.info(f"Gemini client initialized with model: {settings.gemini_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

        # Groq initialization
        self.groq_client = None
        if settings.groq_api_key:
            try:
                from groq import AsyncGroq
                self.groq_client = AsyncGroq(api_key=settings.groq_api_key)
                logger.info(f"Groq client initialized with model: {settings.groq_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")

        # OpenAI initialization
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
            if self.provider == "gemini" and self.gemini_model:
                response_text = await self._generate_gemini(history, user_message)
            elif self.provider == "groq" and self.groq_client:
                response_text = await self._generate_groq(system_prompt, history, user_message)
            elif self.provider == "openai" and self.openai_client:
                response_text = await self._generate_openai(system_prompt, history, user_message)
            else:
                # Automatic fallback cascade
                if self.gemini_model:
                    response_text = await self._generate_gemini(history, user_message)
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

    async def _generate_gemini(self, history: List[Dict[str, str]], user_message: str) -> str:
        # Build chat contents
        chat_contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            chat_contents.append({"role": role, "parts": [msg["content"]]})
        chat_contents.append({"role": "user", "parts": [user_message]})

        response = await self.gemini_model.generate_content_async(
            contents=chat_contents,
            generation_config={"max_output_tokens": 150, "temperature": 0.3}
        )
        return response.text if response and response.text else ""

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

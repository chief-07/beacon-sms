from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # httpSMS Gateway Configuration
    httpsms_api_key: str = Field(default="", description="httpSMS API Key from httpsms.com/settings")
    gateway_phone_number: str = Field(default="", description="Owner phone number on Android SIM in E.164 (+234...)")
    httpsms_signing_key: Optional[str] = Field(default=None, description="Optional webhook signing key")

    # LLM Settings
    llm_provider: str = Field(default="gemini", description="AI provider: gemini | groq | openai")

    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default="gemini-1.5-flash")

    # Groq
    groq_api_key: Optional[str] = Field(default=None)
    groq_model: str = Field(default="llama-3.1-8b-instant")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")

    # SMS Character and Formatting Constraints
    max_sms_characters: int = Field(default=280, description="Target character limit to stay within 2 GSM segments")
    conversation_ttl_minutes: int = Field(default=20, description="TTL in minutes for in-memory session context")
    conversation_history_turns: int = Field(default=3, description="Number of past turns to feed LLM for context")

    # Server configuration
    port: int = Field(default=8000)
    host: str = Field(default="0.0.0.0")
    log_level: str = Field(default="info")


settings = Settings()

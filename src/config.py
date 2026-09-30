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
    gateway_phone_number: str = Field(default="", description="Primary owner phone number on Android SIM in E.164 (+234...)")
    secondary_phone_number: Optional[str] = Field(default=None, description="Optional secondary backup gateway phone number")
    secondary_httpsms_api_key: Optional[str] = Field(default=None, description="Optional secondary httpSMS API Key for backup SIM")
    httpsms_signing_key: Optional[str] = Field(default=None, description="Optional webhook signing key")

    # LLM Settings
    llm_provider: str = Field(default="gemini", description="AI provider: gemini | groq | openai")

    # Google Gemini
    gemini_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default="gemini-3.1-flash-lite")
    gemini_fallback_models: str = Field(
        default="gemini-3.6-flash,gemini-3.8-flash,gemini-flash-latest,gemini-3.1-flash-lite-preview",
        description="Comma-separated fallback Gemini models to use if primary is overloaded or errors"
    )
    gemini_timeout_seconds: float = Field(default=12.0, description="Per-model timeout in seconds before failing over")

    # Groq
    groq_api_key: Optional[str] = Field(default=None)
    groq_model: str = Field(default="llama-3.1-8b-instant")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")

    # SMS Character and Formatting Constraints
    max_sms_characters: int = Field(default=280, description="Target character limit for overall answer")
    sms_split_long_messages: bool = Field(
        default=False,
        description="Split messages >160 chars into standalone single segments (set to False to send single message)"
    )
    sms_segment_delay_seconds: float = Field(
        default=1.5,
        description="Delay in seconds between dispatching consecutive standalone SMS parts"
    )
    block_self_loop: bool = Field(
        default=False,
        description="Temporarily disabled: whether to block gateway numbers from texting themselves or each other"
    )
    conversation_ttl_minutes: int = Field(default=20, description="TTL in minutes for in-memory session context")
    conversation_history_turns: int = Field(default=3, description="Number of past turns to feed LLM for context")

    @property
    def fallback_model_list(self) -> list[str]:
        if not self.gemini_fallback_models:
            return []
        return [m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()]

    # Server configuration
    port: int = Field(default=8000)
    host: str = Field(default="0.0.0.0")
    log_level: str = Field(default="info")


settings = Settings()

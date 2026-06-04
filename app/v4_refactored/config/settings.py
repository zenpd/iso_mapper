"""Centralized configuration — reads from .env via pydantic-settings.

Follows PayOrch standards: environment-scoped settings with type hints,
validation, and support for Azure Key Vault integration.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ────────────────────────────────────────────────────────────────
    app_env: str = Field(default="development", alias="APP_ENV")
    app_secret_key: str = Field(default="change-me-in-production", alias="APP_SECRET_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_allowed_origins: str = Field(default="http://localhost:5173,http://localhost:3000", alias="CORS_ALLOWED_ORIGINS")

    # ── Transformation ─────────────────────────────────────────────────────
    default_approach: Literal["rules", "llm", "hybrid"] = Field(
        default="hybrid",
        alias="TRANSFORMATION_APPROACH"
    )
    max_message_size: int = Field(default=1000000, alias="MAX_MESSAGE_SIZE")
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")

    # ── Azure OpenAI ──────────────────────────────────────────────────────
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_api_key: str = Field(default="", alias="AZURE_API_KEY")
    chat_llm_deployment: str = Field(default="", alias="CHAT_LLM_DEPLOYMENT")
    chat_llm_model: str = Field(default="gpt-4o", alias="CHAT_LLM_MODEL")
    azure_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_API_VERSION")

    # ── Database (optional for future persistence) ────────────────────────
    database_url: str = Field(default="sqlite:///./iso_mapper.db", alias="DATABASE_URL")

    # ── Azure Key Vault (optional) ────────────────────────────────────────
    azure_keyvault_url: str = Field(default="", alias="AZURE_KEYVAULT_URL")
    azure_openai_endpoint_kv_uri: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT_KV_URI")
    azure_api_key_kv_uri: str = Field(default="", alias="AZURE_API_KEY_KV_URI")

    @model_validator(mode="after")
    def validate_settings(self) -> Settings:
        """Validate settings consistency."""
        if self.app_env != "development" and not self.cors_allowed_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must be set for production")
        return self

    @property
    def is_llm_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return bool(
            self.azure_openai_endpoint
            and self.azure_api_key
            and self.chat_llm_deployment
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list."""
        if self.app_env == "development":
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:5173",
            ]
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export for convenience
settings = get_settings()

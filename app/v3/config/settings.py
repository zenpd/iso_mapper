"""
Configuration Management
Centralized configuration using Pydantic settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_api_key: str = Field(default="", alias="AZURE_API_KEY")
    chat_llm_deployment: str = Field(default="", alias="CHAT_LLM_DEPLOYMENT")
    chat_llm_model: str = Field(default="gpt-4o", alias="CHAT_LLM_MODEL")
    azure_api_version: str = Field(default="2024-02-15-preview", alias="AZURE_API_VERSION")
    
    # Application Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_approach: Literal["rules", "llm", "hybrid"] = Field(
        default="hybrid", 
        alias="TRANSFORMATION_APPROACH"
    )
    
    # Performance Settings
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def is_llm_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return bool(
            self.azure_openai_endpoint and 
            self.azure_api_key and 
            self.chat_llm_deployment
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export for convenience
settings = get_settings()

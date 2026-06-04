"""Configuration module."""
from .settings import get_settings, Settings

settings = get_settings()

__all__ = ["settings", "get_settings", "Settings"]

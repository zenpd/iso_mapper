"""Health check and system status endpoints.

Follows PayOrch standards: simple health checks and component status monitoring.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from config.settings import get_settings
from api.schemas import HealthResponse, ConfigResponse
from shared.logger import get_logger

router = APIRouter(prefix="", tags=["System"])
log = get_logger("api.routers.health")
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint — returns system status.
    
    Returns:
        HealthResponse with status and component health
    """
    log.info("health_check_requested")
    
    components = {
        "api": "up",
        "orchestrator": "up",
        "llm": "configured" if settings.is_llm_configured else "not_configured",
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        components=components,
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Get current configuration — returns environment and settings info.
    
    Returns:
        ConfigResponse with active settings
    """
    log.info("config_requested", app_env=settings.app_env)
    
    return ConfigResponse(
        default_approach=settings.default_approach,
        llm_configured=settings.is_llm_configured,
        llm_model=settings.chat_llm_model if settings.is_llm_configured else None,
        cache_enabled=settings.cache_enabled,
        log_level=settings.log_level,
        app_env=settings.app_env,
    )


@router.get("/")
async def root():
    """API root — returns service info.
    
    Returns:
        Service information and available endpoints
    """
    return {
        "service": "ISO 20022 GenAI Migration Platform",
        "version": "3.0.0",
        "description": "Agentic MT to MX transformation following PayOrch architecture",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "config": "GET /config",
            "transform": "POST /api/v1/transform",
            "samples": "GET /api/v1/samples",
            "docs": "GET /docs",
        },
    }

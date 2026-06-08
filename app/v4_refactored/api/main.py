"""FastAPI application entry point — ISO 20022 GenAI Migration Platform.

Follows PayOrch standards: FastAPI with async/await, structured logging,
CORS configuration, router registration, and proper lifespan management.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from shared.logger import setup_logging, get_logger
from observability.tracing import init_tracing
from api.routers import health, transform, reverse_transform, validation

log = get_logger("api.main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management: startup and shutdown.
    
    Context manager that handles application startup and shutdown events.
    Sets up logging and observability on startup, cleans up on shutdown.
    """
    # Startup
    setup_logging(level=settings.log_level)
    init_tracing()
    log.info(
        "api.startup",
        app_env=settings.app_env,
        version="3.0.0",
        llm_configured=settings.is_llm_configured,
    )
    yield
    # Shutdown
    log.info("api.shutdown")


app = FastAPI(
    title="ISO 20022 GenAI Migration Platform",
    description=(
        "Agentic MT to MX transformation using LangGraph agents, "
        "following PayOrch architecture standards"
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# CORS configuration — environment-scoped
_cors_origins = settings.cors_origins_list
if not _cors_origins:
    raise RuntimeError(
        f"CORS configuration invalid for app_env={settings.app_env!r}"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["System"])
app.include_router(transform.router, tags=["Transformation"])
app.include_router(reverse_transform.router, tags=["Reverse Transformation"])
app.include_router(validation.router, tags=["Validation"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

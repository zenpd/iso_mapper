"""
ISO 20022 GenAI Migration Platform - FastAPI Backend
Production-grade API with LangGraph orchestration - FIXED VERSION
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import (
    TransformationRequest, TransformationResponse, TransformationState,
    TransformationApproach
)
from services import orchestrator, llm_service
from utils import get_sample_messages

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("🚀 ISO 20022 GenAI Migration Platform starting...")
    logger.info(f"📋 Default approach: {settings.default_approach}")
    logger.info(f"🤖 LLM configured: {settings.is_llm_configured}")
    yield
    # Shutdown
    logger.info("👋 Platform shutting down...")


app = FastAPI(
    title="ISO 20022 GenAI Migration Platform",
    description="Agentic MT to MX transformation using LangGraph and Azure OpenAI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "ISO 20022 GenAI Migration Platform",
        "version": "2.0.0",
        "status": "running",
        "llm_available": llm_service.is_available,
        "default_approach": settings.default_approach,
        "endpoints": {
            "transform": "POST /transform",
            "samples": "GET /samples",
            "health": "GET /health",
            "config": "GET /config"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "up",
            "orchestrator": "up",
            "llm": "up" if llm_service.is_available else "not_configured"
        }
    }


@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "default_approach": settings.default_approach,
        "llm_configured": settings.is_llm_configured,
        "llm_model": settings.chat_llm_model if settings.is_llm_configured else None,
        "cache_enabled": settings.cache_enabled,
        "log_level": settings.log_level
    }


@app.get("/samples")
async def get_samples():
    """Get sample MT messages for demo"""
    samples = get_sample_messages()
    return {
        "count": len(samples),
        "samples": [s.model_dump() for s in samples]
    }


@app.post("/transform")
async def transform_message(request: TransformationRequest):
    """
    Transform MT message to MX format using agentic AI pipeline
    """
    logger.info(f"📥 Transformation request received - Approach: {request.approach}")
    
    try:
        # Create transformation state
        state = TransformationState(
            raw_mt_message=request.mt_message,
            message_id=request.message_id,
            approach=request.approach
        )
        
        # Execute transformation
        result = await orchestrator.transform(state)
        
        # Debug logging
        logger.info(f"Transform result keys: {result.keys()}")
        logger.info(f"Success: {result.get('success')}")
        
        if not result.get("success"):
            error_msg = result.get("error", "Transformation failed")
            logger.error(f"Transformation failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        # Build response
        parsed_mt = result.get("parsed_mt", {})
        mx_output = result.get("mx_output", {})
        agent_results = result.get("agent_results", {})
        validation = result.get("validation_result", {})
        
        # Calculate statistics
        mapping_result = result.get("mapping_result", {})
        enrichment_result = result.get("enrichment_result", {})
        
        statistics = {
            "total_duration_ms": result.get("total_duration_ms", 0),
            "fields_parsed": parsed_mt.get("field_count", 0),
            "fields_mapped": mapping_result.get("fields_mapped", 0),
            "fields_enriched": enrichment_result.get("fields_added", 0),
            "overall_confidence": mapping_result.get("overall_confidence", 0),
            "validation_score": validation.get("compliance_score", 0),
            "errors": len(validation.get("errors", [])),
            "warnings": len(validation.get("warnings", []))
        }
        
        response_data = {
            "success": True,
            "message_id": parsed_mt.get("message_id", "unknown"),
            "mt_type": parsed_mt.get("message_type", "MTXXX"),
            "mx_type": mx_output.get("mx_type", "pacs.XXX"),
            "approach_used": request.approach.value,
            "parsed_mt": parsed_mt,
            "mx_structure": mx_output.get("structure", {}),
            "mx_xml": mx_output.get("xml", ""),
            "agent_results": agent_results,
            "statistics": statistics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Transformation complete - {response_data['message_id']}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transformation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
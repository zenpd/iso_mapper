"""Transformation endpoints — MT to MX conversion API.

Follows PayOrch standards: RESTful API with proper request/response validation,
error handling, and comprehensive logging.
"""
from __future__ import annotations

import sys
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from api.schemas import (
    TransformationRequest,
    TransformationResponse,
    SamplesResponse,
    SampleMessage,
)
from shared.logger import get_logger

router = APIRouter(prefix="/api/v1", tags=["Transformation"])
log = get_logger("api.routers.transformation")

router = APIRouter(prefix="/api/v1", tags=["Transformation"])
log = get_logger("api.routers.transformation")


def get_sample_messages() -> List[SampleMessage]:
    """Get sample MT messages for demonstration.
    
    Returns:
        List of sample messages
    """
    return [
        SampleMessage(
            id="sample-001",
            name="International Transfer",
            description="Cross-border SWIFT MT103 payment",
            message=":20:REFERENCE123\n:23B:CRED\n:32A:250101USD1000000,00\n:50K:SENDER BANK\n:59:/BENEFICIARY\n:70:PAYMENT FOR INVOICE",
            currency="USD",
            amount="1,000,000.00",
        ),
        SampleMessage(
            id="sample-002",
            name="Domestic Transfer",
            description="Domestic SWIFT MT202 bank transfer",
            message=":20:DOM-REF456\n:21:CORR-REF\n:32A:250102EUR500000,00\n:50F:SENDING BANK\n:59:/RECEIVING BANK",
            currency="EUR",
            amount="500,000.00",
        ),
    ]


@router.get("/samples", response_model=SamplesResponse)
async def get_samples():
    """Get sample MT messages for testing.
    
    Returns:
        SamplesResponse with list of sample messages
    """
    log.info("samples_requested")
    samples = get_sample_messages()
    return SamplesResponse(count=len(samples), samples=samples)


@router.post("/transform", response_model=TransformationResponse)
async def transform_message(request: TransformationRequest) -> TransformationResponse:
    """Transform SWIFT MT message to ISO 20022 MX format.
    
    This is the main transformation endpoint. It processes a SWIFT MT message through
    a pipeline of agents:
    1. Parser: Extracts fields from MT message
    2. Mapping: Maps MT fields to MX schema
    3. Enrichment: Adds regulatory/mandatory fields
    4. Validation: Checks compliance
    5. Generator: Produces final MX XML
    
    Args:
        request: TransformationRequest with MT message and approach
    
    Returns:
        TransformationResponse with parsed MT, generated MX, and statistics
    
    Raises:
        HTTPException: If transformation fails
    """
    log.info("transformation_requested", approach=request.approach)

    try:
        # Lazy import v4 orchestrator to avoid module-level import conflicts
        if '/v4' not in sys.path:
            sys.path.insert(0, '/v4')
        from services.orchestrator import TransformationOrchestrator
        from models.schemas import TransformationState as V4State, TransformationApproach as V4Approach

        approach_map = {"rules": V4Approach.RULES, "llm": V4Approach.LLM, "hybrid": V4Approach.HYBRID}
        v4_approach = approach_map.get(request.approach.value, V4Approach.HYBRID)

        orchestrator = TransformationOrchestrator()
        state = V4State(
            raw_mt_message=request.mt_message,
            message_id=request.message_id,
            approach=v4_approach,
        )

        result = await orchestrator.transform(state)

        parsed_mt = result.get("parsed_mt", {})
        mapping = result.get("mapping_result", {})
        enrichment = result.get("enrichment_result", {})
        validation = result.get("validation_result", {})
        mx_out = result.get("mx_output", {})
        agent_res = result.get("agent_results", {})

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Transformation failed"))

        mt_type = parsed_mt.get("message_type", "MT103")
        mx_type = mx_out.get("mx_type", "pacs.008")

        fields_parsed = parsed_mt.get("field_count", 0)
        fields_mapped = mapping.get("fields_mapped", 0)
        fields_enriched = enrichment.get("fields_added", 0)
        overall_confidence = mapping.get("overall_confidence", 0.0)
        val_score = validation.get("compliance_score", 0.0) if validation else 0.0
        val_errors = len(validation.get("errors", [])) if validation else 0
        val_warnings = len(validation.get("warnings", [])) if validation else 0

        response = TransformationResponse(
            success=True,
            message_id=result.get("message_id", request.message_id or "msg-001"),
            mt_type=mt_type,
            mx_type=mx_type,
            approach_used=result.get("approach", request.approach.value),
            parsed_mt=parsed_mt,
            mx_structure=mx_out.get("structure", {}),
            mx_xml=mx_out.get("xml", ""),
            agent_results={k: (v if isinstance(v, dict) else v.model_dump()) for k, v in agent_res.items()},
            statistics={
                "total_duration_ms": result.get("total_duration_ms", 0),
                "fields_parsed": fields_parsed,
                "fields_mapped": fields_mapped,
                "fields_enriched": fields_enriched,
                "overall_confidence": overall_confidence,
                "validation_score": val_score * 100 if val_score <= 1 else val_score,
                "errors": val_errors,
                "warnings": val_warnings,
            },
            timestamp=datetime.utcnow().isoformat(),
        )

        log.info("transformation_complete", message_id=response.message_id, mt_type=mt_type, mx_type=mx_type)
        return response

    except HTTPException:
        raise
    except Exception as e:
        log.error("transformation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

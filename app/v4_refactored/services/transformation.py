"""Transformation service — main orchestration logic.

Coordinates the transformation pipeline:
1. Parsing MT message
2. Mapping MT fields to MX schema
3. Enriching with mandatory fields
4. Validating output
5. Generating final XML

This service integrates all agents and produces the final result.
"""
from __future__ import annotations

from datetime import datetime

from api.schemas import TransformationRequest, TransformationResponse, TransformationState
from shared.logger import get_logger

log = get_logger("services.transformation")


class TransformationService:
    """Service for coordinating MT to MX transformation pipeline."""

    async def transform(self, request: TransformationRequest) -> TransformationResponse:
        """Execute transformation pipeline.
        
        Args:
            request: Transformation request with MT message and approach
        
        Returns:
            TransformationResponse with results and statistics
        
        Raises:
            Exception: If transformation fails
        """
        log.info(
            "transformation_service.started",
            approach=request.approach.value,
            has_message_id=request.message_id is not None,
        )

        try:
            # Initialize transformation state
            state = TransformationState(
                raw_mt_message=request.mt_message,
                message_id=request.message_id,
                approach=request.approach,
            )

            # TODO: Integrate actual agents
            # For now, this is a placeholder showing the structure

            # Step 1: Parse MT message
            # parsed_state = await self.parse_mt(state)

            # Step 2: Map to MX
            # mapped_state = await self.map_to_mx(parsed_state)

            # Step 3: Enrich
            # enriched_state = await self.enrich(mapped_state)

            # Step 4: Validate
            # validated_state = await self.validate(enriched_state)

            # Step 5: Generate XML
            # final_state = await self.generate_xml(validated_state)

            # Record completion time
            state.completed_at = datetime.utcnow()
            state.success = True

            # Build response
            response = self._build_response(state)

            log.info(
                "transformation_service.complete",
                message_id=response.message_id,
                duration_ms=response.statistics.total_duration_ms,
            )

            return response

        except Exception as e:
            log.error("transformation_service.failed", error=str(e))
            raise

    def _build_response(self, state: TransformationState) -> TransformationResponse:
        """Build API response from transformation state.
        
        Args:
            state: Completed transformation state
        
        Returns:
            TransformationResponse formatted for API
        """
        duration_ms = (
            int((state.completed_at - state.started_at).total_seconds() * 1000)
            if state.completed_at
            else 0
        )

        return TransformationResponse(
            success=state.success,
            message_id=state.message_id or "unknown",
            mt_type=state.parsed_mt.message_type if state.parsed_mt else "MT???",
            mx_type=state.parsed_mt.mx_equivalent if state.parsed_mt else "pacs.???",
            approach_used=state.approach.value,
            parsed_mt=state.parsed_mt.model_dump() if state.parsed_mt else {},
            mx_structure=state.mx_output.structure if state.mx_output else {},
            mx_xml=state.mx_output.xml if state.mx_output else "",
            agent_results={
                name: result.model_dump() for name, result in state.agent_results.items()
            },
            statistics={
                "total_duration_ms": duration_ms,
                "fields_parsed": state.parsed_mt.field_count if state.parsed_mt else 0,
                "fields_mapped": state.mapping_result.fields_mapped if state.mapping_result else 0,
                "fields_enriched": state.enrichment_result.fields_added if state.enrichment_result else 0,
                "overall_confidence": state.mapping_result.overall_confidence if state.mapping_result else 0.0,
                "validation_score": state.validation_result.compliance_score if state.validation_result else 0.0,
                "errors": len(state.validation_result.errors) if state.validation_result else 0,
                "warnings": len(state.validation_result.warnings) if state.validation_result else 0,
            },
            timestamp=datetime.utcnow().isoformat(),
            error=state.error,
        )

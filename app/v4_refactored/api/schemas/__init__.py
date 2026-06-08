"""API schemas package."""
from .transformation import (
    TransformationApproach,
    TransformationRequest,
    TransformationResponse,
    MappedField,
    ValidationError,
    StatisticsData,
    ErrorResponse,
    HealthResponse,
    ConfigResponse,
    SampleMessage,
    SamplesResponse,
)
from .state import (
    AgentStatus,
    ParsedMTMessage,
    MappingResult,
    EnrichmentResult,
    ValidationResult,
    MXOutput,
    AgentResult,
    TransformationState,
)

__all__ = [
    # Transformation schemas
    "TransformationApproach",
    "TransformationRequest",
    "TransformationResponse",
    "MappedField",
    "ValidationError",
    "StatisticsData",
    "ErrorResponse",
    "HealthResponse",
    "ConfigResponse",
    "SampleMessage",
    "SamplesResponse",
    # State schemas
    "AgentStatus",
    "ParsedMTMessage",
    "MappingResult",
    "EnrichmentResult",
    "ValidationResult",
    "MXOutput",
    "AgentResult",
    "TransformationState",
]

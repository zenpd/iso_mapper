"""API request/response schemas — Pydantic v2 models.

Follows PayOrch standards: strongly typed API contracts with validation.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TransformationApproach(str, Enum):
    """Available transformation approaches."""

    RULES = "rules"
    LLM = "llm"
    HYBRID = "hybrid"


class TransformationRequest(BaseModel):
    """API request for MT to MX transformation.
    
    Attributes:
        mt_message: Raw SWIFT MT message text
        approach: Transformation strategy (rules, llm, or hybrid)
        message_id: Optional unique identifier for this transformation
    """

    mt_message: str = Field(
        ..., description="Raw SWIFT MT message text", min_length=1
    )
    approach: TransformationApproach = Field(
        default=TransformationApproach.HYBRID,
        description="Transformation approach: rules, llm, or hybrid",
    )
    message_id: Optional[str] = Field(
        default=None, description="Optional unique message identifier"
    )


class MappedField(BaseModel):
    """Represents a single mapped field from MT to MX.
    
    Attributes:
        value: The field value
        confidence: Confidence score [0, 1]
        reasoning: Explanation of how field was mapped
        source_field: Original MT field
        method: How the field was determined
        mx_path: ISO 20022 MX path
    """

    value: Any
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    source_field: str
    method: Literal["rule", "llm", "inferred", "generated", "enriched"]
    mx_path: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error or warning.
    
    Attributes:
        error_type: Type of validation error
        field: Field that failed validation
        message: Error description
        severity: Error level (error, warning, info)
        suggestion: Optional fix suggestion
    """

    error_type: str
    field: str
    message: str
    severity: Literal["error", "warning", "info"]
    suggestion: Optional[str] = None


class StatisticsData(BaseModel):
    """Transformation statistics.
    
    Attributes:
        total_duration_ms: Total execution time in milliseconds
        fields_parsed: Number of fields parsed from MT
        fields_mapped: Number of fields mapped to MX
        fields_enriched: Number of fields enriched
        overall_confidence: Average confidence across mappings
        validation_score: Compliance score [0, 100]
        errors: Number of validation errors
        warnings: Number of validation warnings
    """

    total_duration_ms: int
    fields_parsed: int
    fields_mapped: int
    fields_enriched: int
    overall_confidence: float
    validation_score: float
    errors: int
    warnings: int


class TransformationResponse(BaseModel):
    """API response for successful transformation.
    
    Attributes:
        success: Whether transformation succeeded
        message_id: Unique identifier for this transformation
        mt_type: Type of SWIFT message (e.g., MT103)
        mx_type: Type of MX message (e.g., pacs.008)
        approach_used: Transformation approach that was used
        parsed_mt: Parsed fields from input MT message
        mx_structure: Generated MX structure as nested dict
        mx_xml: Generated ISO 20022 XML string
        agent_results: Details from each agent in pipeline
        statistics: Performance and quality metrics
        timestamp: ISO 8601 timestamp
        error: Error description if failed
    """

    success: bool
    message_id: str
    mt_type: str
    mx_type: str
    approach_used: str
    parsed_mt: Dict[str, Any]
    mx_structure: Dict[str, Any]
    mx_xml: str
    agent_results: Dict[str, Dict[str, Any]]
    statistics: StatisticsData
    timestamp: str
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    timestamp: str
    components: Dict[str, str] = Field(
        default_factory=lambda: {
            "api": "up",
            "orchestrator": "up",
            "llm": "checking",
        }
    )


class ConfigResponse(BaseModel):
    """Configuration response."""

    default_approach: str
    llm_configured: bool
    llm_model: Optional[str] = None
    cache_enabled: bool
    log_level: str
    app_env: str


class SampleMessage(BaseModel):
    """Sample MT message for demo purposes.
    
    Attributes:
        id: Unique identifier
        name: Friendly name
        description: What this sample demonstrates
        message: Raw SWIFT MT message
        currency: Currency code
        amount: Transaction amount
    """

    id: str
    name: str
    description: str
    message: str
    currency: str
    amount: str


class SamplesResponse(BaseModel):
    """Response containing sample messages.
    
    Attributes:
        count: Number of samples
        samples: List of sample messages
    """

    count: int
    samples: List[SampleMessage]

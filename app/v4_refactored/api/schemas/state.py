"""Internal state models for transformation pipeline.

These are internal to the application and flow through the LangGraph agent workflow.
Not exposed directly in API responses.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .transformation import TransformationApproach


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETE = "complete"
    WARNING = "warning"
    ERROR = "error"


class ParsedMTMessage(BaseModel):
    """Parsed MT message structure (internal).
    
    Attributes:
        message_id: Unique identifier
        message_type: MT type (e.g., MT103)
        mx_equivalent: Equivalent MX type (e.g., pacs.008)
        fields: Extracted fields
        field_count: Total fields parsed
        raw: Original raw message
        parsed_at: Timestamp
    """

    message_id: str
    message_type: str
    mx_equivalent: str
    fields: Dict[str, Any]
    field_count: int
    raw: str
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


class MappingResult(BaseModel):
    """Result from mapping agent (internal).
    
    Attributes:
        mapped_fields: Dict of field names to MappedField
        fields_mapped: Count of mapped fields
        overall_confidence: Average confidence
        low_confidence_fields: Fields with low confidence
        approach_used: Which approach was used
    """

    mapped_fields: Dict[str, Any]
    fields_mapped: int
    overall_confidence: float
    low_confidence_fields: List[str] = Field(default_factory=list)
    approach_used: TransformationApproach


class EnrichmentResult(BaseModel):
    """Result from enrichment agent (internal).
    
    Attributes:
        enriched_data: Enriched fields
        fields_added: Count of fields added
        enrichment_log: Log of enrichment operations
        regulatory_compliance: Compliance flags
    """

    enriched_data: Dict[str, Any]
    fields_added: int
    enrichment_log: List[str] = Field(default_factory=list)
    regulatory_compliance: Dict[str, bool] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result from validation agent (internal).
    
    Attributes:
        is_valid: Whether validation passed
        compliance_score: Score 0-100
        errors: List of errors
        warnings: List of warnings
        auto_corrections: Suggested corrections
    """

    is_valid: bool
    compliance_score: float
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    auto_corrections: List[Dict[str, Any]] = Field(default_factory=list)


class MXOutput(BaseModel):
    """Generated MX message output (internal).
    
    Attributes:
        mx_type: MX message type
        version: Message version
        structure: Complete MX structure
        xml: Generated XML string
        generated_at: Timestamp
    """

    mx_type: str
    version: str
    structure: Dict[str, Any]
    xml: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentResult(BaseModel):
    """Result from a single agent execution (internal).
    
    Attributes:
        agent_name: Name of agent
        status: Execution status
        message: Status message
        confidence: Confidence score
        fields_processed: Count of fields processed
        duration_ms: Execution time
        details: Additional details
        timestamp: When it ran
    """

    agent_name: str
    status: AgentStatus
    message: str
    confidence: Optional[float] = None
    fields_processed: int = 0
    duration_ms: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TransformationState(BaseModel):
    """LangGraph state flowing through transformation pipeline.
    
    This is the internal state that flows through all agents in the pipeline.
    It accumulates results as each agent processes the message.
    
    Attributes:
        raw_mt_message: Input SWIFT MT message
        message_id: Unique identifier
        approach: Transformation approach to use
        parsed_mt: Result of parsing
        mapping_result: Result of mapping
        enrichment_result: Result of enrichment
        validation_result: Result of validation
        mx_output: Generated MX output
        agent_results: Tracking of all agent executions
        started_at: Pipeline start time
        completed_at: Pipeline completion time
        total_duration_ms: Total pipeline execution time
        success: Whether pipeline succeeded
        error: Error message if failed
    """

    # Input
    raw_mt_message: str
    message_id: Optional[str] = None
    approach: TransformationApproach = TransformationApproach.HYBRID

    # Pipeline state (filled by agents)
    parsed_mt: Optional[ParsedMTMessage] = None
    mapping_result: Optional[MappingResult] = None
    enrichment_result: Optional[EnrichmentResult] = None
    validation_result: Optional[ValidationResult] = None
    mx_output: Optional[MXOutput] = None

    # Agent tracking
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)

    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0
    success: bool = False
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

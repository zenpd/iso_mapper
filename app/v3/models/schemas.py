"""
Data Models
Pydantic models for type safety and validation
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from enum import Enum


class TransformationApproach(str, Enum):
    """Available transformation approaches"""
    RULES = "rules"
    LLM = "llm"
    HYBRID = "hybrid"


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETE = "complete"
    WARNING = "warning"
    ERROR = "error"


class MappedField(BaseModel):
    """Represents a single mapped field"""
    value: Any
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    source_field: str
    method: Literal["rule", "llm", "inferred", "generated", "enriched"]
    mx_path: Optional[str] = None


class AgentResult(BaseModel):
    """Result from an agent execution"""
    agent_name: str
    status: AgentStatus
    message: str
    confidence: Optional[float] = None
    fields_processed: int = 0
    duration_ms: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ParsedMTMessage(BaseModel):
    """Parsed MT message structure"""
    message_id: str
    message_type: str
    mx_equivalent: str
    fields: Dict[str, Any]
    field_count: int
    raw: str
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


class MappingResult(BaseModel):
    """Result from mapping agent"""
    mapped_fields: Dict[str, MappedField]
    fields_mapped: int
    overall_confidence: float
    low_confidence_fields: List[str] = Field(default_factory=list)
    approach_used: TransformationApproach


class EnrichmentResult(BaseModel):
    """Result from enrichment agent"""
    enriched_data: Dict[str, MappedField]
    fields_added: int
    enrichment_log: List[str]
    regulatory_compliance: Dict[str, bool] = Field(default_factory=dict)


class ValidationError(BaseModel):
    """Validation error details"""
    error_type: str
    field: str
    message: str
    severity: Literal["error", "warning", "info"]
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Result from validation agent"""
    is_valid: bool
    compliance_score: float
    errors: List[ValidationError]
    warnings: List[ValidationError]
    auto_corrections: List[Dict[str, Any]] = Field(default_factory=list)


class MXOutput(BaseModel):
    """Generated MX message output"""
    mx_type: str
    version: str
    structure: Dict[str, Any]
    xml: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TransformationState(BaseModel):
    """
    LangGraph state that flows through the transformation pipeline
    """
    # Input
    raw_mt_message: str
    message_id: Optional[str] = None
    approach: TransformationApproach = TransformationApproach.HYBRID
    
    # Pipeline state
    parsed_mt: Optional[ParsedMTMessage] = None
    mapping_result: Optional[MappingResult] = None
    enrichment_result: Optional[EnrichmentResult] = None
    validation_result: Optional[ValidationResult] = None
    mx_output: Optional[MXOutput] = None
    
    # Agent results for tracking
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0
    success: bool = False
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class TransformationRequest(BaseModel):
    """API request for transformation"""
    mt_message: str
    approach: TransformationApproach = TransformationApproach.HYBRID
    message_id: Optional[str] = None


class TransformationResponse(BaseModel):
    """API response for transformation"""
    success: bool
    message_id: str
    mt_type: str
    mx_type: str
    approach_used: str
    
    # Results
    parsed_mt: Dict[str, Any]
    mx_structure: Dict[str, Any]
    mx_xml: str
    
    # Agent tracking
    agent_results: Dict[str, Dict[str, Any]]
    
    # Statistics
    statistics: Dict[str, Any]
    
    # Metadata
    timestamp: str
    error: Optional[str] = None


class SampleMessage(BaseModel):
    """Sample MT message for demo"""
    id: str
    name: str
    description: str
    message: str
    currency: str
    amount: str

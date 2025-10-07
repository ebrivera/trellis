"""
Shared Pydantic schemas used across all workflow templates.
Template-specific models are in src/templates/
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class Channel(str, Enum):
    """Communication channels for notifications"""
    SMS = "sms"
    EMAIL = "email"


class EntityType(str, Enum):
    """Maps to database tables"""
    PERSON = "people"
    GROUP = "groups"
    GIFT = "gifts"


class MatchStrategy(str, Enum):
    """Strategies for matching algorithm"""
    CAPACITY_BALANCED = "capacity_balanced"
    INTEREST_OVERLAP = "interest_overlap"
    PROXIMITY = "proximity"


class TemplateType(str, Enum):
    """The 3 workflow templates"""
    MATCHING = "matching"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"


# ============================================================================
# SHARED BUILDING BLOCKS
# ============================================================================

class FilterCondition(BaseModel):
    """A single filter condition for querying entities"""
    field: str = Field(..., description="Field name to filter on (e.g., 'capacity', 'visit_date')")
    operator: Literal["=", ">", ">=", "<", "<=", "!=", "contains"] = Field(
        default="=",
        description="Comparison operator"
    )
    value: str = Field(..., description="Value to compare (will be converted to appropriate type)")

    class Config:
        # Required for OpenAI Structured Outputs
        extra = "forbid"


class EntitySource(BaseModel):
    """DEPRECATED: Use EntityQuery instead. Kept for backward compatibility."""
    file: str = Field(..., description="CSV filename (e.g., 'volunteers.csv')")
    entity_type: EntityType = Field(..., description="Type of entity in this file")
    filters: Optional[List[str]] = Field(
        default=None,
        description="SQL-like filter conditions (e.g., 'availability_days LIKE \"%Sun%\"')"
    )

    @field_validator('file')
    @classmethod
    def validate_file_extension(cls, v: str) -> str:
        if not v.endswith('.csv'):
            raise ValueError("File must be a CSV")
        return v


class EntityQuery(BaseModel):
    """Query specification for loading entities from database"""
    entity_type: EntityType = Field(..., description="Which table to query (people, groups, gifts)")
    subtype: Optional[str] = Field(
        default=None,
        description="Row filter: person_type (volunteer, visitor, mentor, mentee, donor) or group_type (role, initiative, team)"
    )
    filters: Optional[List[FilterCondition]] = Field(
        default=None,
        description="Additional filter conditions"
    )

    @field_validator('subtype')
    @classmethod
    def validate_subtype(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return v

        entity_type = info.data.get('entity_type')

        # Valid person subtypes
        if entity_type == EntityType.PERSON:
            valid_subtypes = ['volunteer', 'visitor', 'mentor', 'mentee', 'donor', 'leader']
            if v not in valid_subtypes:
                raise ValueError(f"Invalid person_type: {v}. Must be one of {valid_subtypes}")

        # Valid group subtypes
        elif entity_type == EntityType.GROUP:
            valid_subtypes = ['role', 'initiative', 'team']
            if v not in valid_subtypes:
                raise ValueError(f"Invalid group_type: {v}. Must be one of {valid_subtypes}")

        # Gifts don't have subtypes
        elif entity_type == EntityType.GIFT and v is not None:
            raise ValueError("EntityType.GIFT does not support subtypes")

        return v

    class Config:
        # Required for OpenAI Structured Outputs
        extra = "forbid"


class NotificationConfig(BaseModel):
    """Configuration for a notification to be sent"""
    recipient_type: Optional[str] = Field(
        default=None,
        description="Who receives this (e.g., 'source', 'target_owners', 'flagged_donors')"
    )
    recipient: Optional[str] = Field(
        default=None,
        description="Specific email/phone if not using recipient_type"
    )
    channel: Channel = Field(..., description="SMS or email")
    template: str = Field(..., description="Handlebars template string with {{variables}}")

    @field_validator('recipient_type', 'recipient')
    @classmethod
    def validate_recipient(cls, v, info):
        # At least one of recipient_type or recipient must be provided
        values = info.data
        if 'recipient_type' in values and 'recipient' in values:
            if not values.get('recipient_type') and not values.get('recipient'):
                raise ValueError("Must specify either recipient_type or recipient")
        return v


# ============================================================================
# CLASSIFIER OUTPUT
# ============================================================================

class TemplateChoice(BaseModel):
    """Output from the classifier node"""
    template: TemplateType = Field(..., description="Which workflow template to use")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Why this template was chosen")
    clarifying_question: Optional[str] = Field(
        default=None,
        description="Question to ask user if confidence < 0.8"
    )


# ============================================================================
# GRAPH STATE
# ============================================================================

class OrchestratorState(BaseModel):
    """State object passed between LangGraph nodes"""
    # Input
    request: str = Field(..., description="Natural language request from user")
    available_files: List[str] = Field(
        default_factory=list,
        description="List of CSV files available for this request"
    )
    
    # Classifier output
    template: Optional[TemplateType] = None
    confidence: Optional[float] = None
    
    # Extractor output
    params: Optional[Dict[str, Any]] = None  # Will be MatchingParams | MonitoringParams | AnalysisParams
    
    # Execution output
    approval_id: Optional[str] = None
    execution_status: Optional[str] = None
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    clarifications: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# EXECUTION PREVIEWS (for approval gate)
# ============================================================================

class MatchingPreview(BaseModel):
    """Preview data for matching workflow approval"""
    proposed_assignments: int
    unmatched_source: int
    unmatched_target: int
    match_rate: float = Field(ge=0.0, le=1.0)
    avg_match_score: float = Field(ge=0.0, le=1.0)
    assignments_table: List[Dict[str, Any]]  # source_id, target_id, score, etc.


class MonitoringPreview(BaseModel):
    """Preview data for monitoring workflow approval"""
    flagged_count: int
    avg_threshold_exceeded_by: str  # e.g., "18 days"
    flagged_entities: List[Dict[str, Any]]
    alert_recipients: List[str]
    optional_notification_count: Optional[int] = None


class AnalysisPreview(BaseModel):
    """Preview data for analysis workflow approval"""
    metrics_summary: Dict[str, Any]
    flagged_entities: Optional[List[Dict[str, Any]]] = None
    notification_count: int
    dashboard_data: Dict[str, Any]


# ============================================================================
# APPROVAL GATE
# ============================================================================

class ApprovalGate(BaseModel):
    """Data stored in approval_gates table"""
    id: str = Field(..., description="UUID for this approval")
    template: TemplateType
    params: Dict[str, Any]  # JSON blob of MatchingParams | MonitoringParams | AnalysisParams
    preview_data: Dict[str, Any]  # MatchingPreview | MonitoringPreview | AnalysisPreview
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: str  # ISO timestamp
    resolved_at: Optional[str] = None
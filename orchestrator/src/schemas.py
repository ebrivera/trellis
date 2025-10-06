"""
Pydantic schemas for the 3 workflow templates.
These enforce the structure of params extracted by the LLM.
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================================
# ENUMS & SHARED MODELS
# ============================================================================

class Channel(str, Enum):
    """Communication channels for notifications"""
    SMS = "sms"
    EMAIL = "email"


class EntityType(str, Enum):
    """Fixed entity types matching DB schema"""
    PERSON = "Person"
    ROLE = "Role"
    GROUP = "Group"
    GIFT = "Gift"
    INITIATIVE = "Initiative"


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
# COMMON BUILDING BLOCKS
# ============================================================================

class EntitySource(BaseModel):
    """Represents a data source (CSV file) for an entity type"""
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
# TEMPLATE CHOICE (Classifier Output)
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
# MATCHING TEMPLATE
# ============================================================================

class MatchFields(BaseModel):
    """Which fields to score on for matching"""
    score_on: List[str] = Field(..., description="Field names to compare (e.g., ['interests', 'zip'])")
    weights: Dict[str, float] = Field(..., description="Weight for each field (must sum to 1.0)")

    @field_validator('weights')
    @classmethod
    def validate_weights_sum(cls, v: Dict[str, float]) -> Dict[str, float]:
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class MatchConstraints(BaseModel):
    """Constraints for matching algorithm"""
    max_per_target: Optional[str] = Field(
        default=None,
        description="Field name in target entity that specifies capacity (e.g., 'sunday_count')"
    )
    respect_preferences: bool = Field(
        default=True,
        description="Whether to consider user preferences in matching"
    )
    min_score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum match score to accept (0-1)"
    )


class MatchingParams(BaseModel):
    """Parameters for the Matching template"""
    template: Literal[TemplateType.MATCHING] = TemplateType.MATCHING
    source: EntitySource = Field(..., description="Entities to be assigned (volunteers, mentees)")
    target: EntitySource = Field(..., description="Targets to assign to (roles, mentors)")
    match_strategy: MatchStrategy = Field(
        default=MatchStrategy.CAPACITY_BALANCED,
        description="Algorithm to use for matching"
    )
    match_fields: MatchFields = Field(..., description="Which fields to score on")
    constraints: MatchConstraints = Field(
        default_factory=MatchConstraints,
        description="Constraints for matching"
    )
    notifications: List[NotificationConfig] = Field(
        default_factory=list,
        description="Notifications to send after approval"
    )


# ============================================================================
# MONITORING TEMPLATE
# ============================================================================

class TimeCondition(BaseModel):
    """Time-based condition for monitoring"""
    time_field: str = Field(..., description="Date field to check (e.g., 'visit_date')")
    threshold: str = Field(..., description="Time threshold (e.g., '14 days', '90 days')")
    operator: Literal[">", "<", ">=", "<=", "="] = Field(
        default=">",
        description="Comparison operator"
    )
    additional_filters: Optional[List[str]] = Field(
        default=None,
        description="Extra SQL-like conditions (e.g., 'last_contact_date IS NULL')"
    )

    @field_validator('threshold')
    @classmethod
    def validate_threshold_format(cls, v: str) -> str:
        # Basic validation that it looks like "N days/weeks/months"
        parts = v.split()
        if len(parts) != 2:
            raise ValueError("Threshold must be in format 'N days|weeks|months'")
        try:
            int(parts[0])
        except ValueError:
            raise ValueError(f"Threshold must start with a number, got '{parts[0]}'")
        if parts[1] not in ['day', 'days', 'week', 'weeks', 'month', 'months']:
            raise ValueError(f"Threshold unit must be days/weeks/months, got '{parts[1]}'")
        return v


class Alert(BaseModel):
    """Alert configuration for monitoring"""
    recipient: str = Field(..., description="Email or phone to send alert to")
    channel: Channel = Field(..., description="SMS or email")
    template: str = Field(..., description="Alert message template")


class OptionalAction(BaseModel):
    """Optional follow-up action after monitoring alert"""
    type: Literal["bulk_notification"] = Field(..., description="Type of action")
    recipients: str = Field(..., description="Who gets the follow-up (e.g., 'flagged_visitors')")
    channel: Channel = Field(..., description="SMS or email")
    template: str = Field(..., description="Message template")
    requires_approval: bool = Field(default=True, description="Whether this needs approval")


class MonitoringParams(BaseModel):
    """Parameters for the Monitoring template"""
    template: Literal[TemplateType.MONITORING] = TemplateType.MONITORING
    source: EntitySource = Field(..., description="Data to monitor (visitors, donors)")
    condition: TimeCondition = Field(..., description="Time-based trigger condition")
    alerts: List[Alert] = Field(..., description="Who to alert when condition is met")
    optional_action: Optional[OptionalAction] = Field(
        default=None,
        description="Optional follow-up action (e.g., send bulk SMS to flagged entities)"
    )


# ============================================================================
# ANALYSIS TEMPLATE
# ============================================================================

class MetricFormula(BaseModel):
    """A metric to calculate"""
    name: str = Field(..., description="Metric name (e.g., 'total_raised')")
    formula: str = Field(..., description="SQL-like formula (e.g., 'SUM(amount)')")
    group_by: Optional[str] = Field(
        default=None,
        description="Field to group by (e.g., 'initiative_name')"
    )
    format: Optional[Literal["currency", "percent", "number"]] = Field(
        default="number",
        description="How to format the result"
    )


class FlagCondition(BaseModel):
    """Condition to flag entities for attention"""
    name: str = Field(..., description="Flag name (e.g., 'lapsed_donors')")
    condition: str = Field(..., description="SQL-like condition to detect outliers")
    group_by: Optional[str] = Field(
        default=None,
        description="Field to group by (e.g., 'donor_id')"
    )
    action: Literal["notify", "flag", "report"] = Field(
        default="flag",
        description="What to do with flagged entities"
    )


class AnalysisParams(BaseModel):
    """Parameters for the Analysis template"""
    template: Literal[TemplateType.ANALYSIS] = TemplateType.ANALYSIS
    sources: List[EntitySource] = Field(..., description="Data sources to analyze")
    join_on: Optional[str] = Field(
        default=None,
        description="Field to join sources on (e.g., 'initiative_name')"
    )
    metrics: List[MetricFormula] = Field(..., description="Metrics to calculate")
    flags: Optional[List[FlagCondition]] = Field(
        default=None,
        description="Conditions to flag outliers/issues"
    )
    notifications: List[NotificationConfig] = Field(
        default_factory=list,
        description="Notifications to send after approval"
    )

    @field_validator('sources')
    @classmethod
    def validate_multiple_sources(cls, v: List[EntitySource]) -> List[EntitySource]:
        if len(v) < 1:
            raise ValueError("Analysis requires at least one data source")
        return v


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
        # Allow arbitrary types for flexibility
        arbitrary_types_allowed = True


# ============================================================================
# EXECUTION RESULTS (for approval gate preview)
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


# ============================================================================
# HELPER: Get params model class by template type
# ============================================================================

def get_params_model(template: TemplateType):
    """Return the appropriate Pydantic model for a template type"""
    if template == TemplateType.MATCHING:
        return MatchingParams
    elif template == TemplateType.MONITORING:
        return MonitoringParams
    elif template == TemplateType.ANALYSIS:
        return AnalysisParams
    else:
        raise ValueError(f"Unknown template type: {template}")
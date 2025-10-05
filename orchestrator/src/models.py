from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal

# ============ GoalSpec ============
class GoalSpec(BaseModel):
    """Normalized, structured representation of what the user wants."""
    objective: str = Field(..., description="Single-sentence goal")
    constraints: List[str] = Field(default_factory=list, description="Hard rules: no X, only Y, etc.")
    kpis: List[str] = Field(default_factory=list, description="Metrics to track success")
    inputs_required: List[str] = Field(default_factory=list, description="Data sources needed: people_sheet, groups_sheet, etc.")
    assumptions: List[str] = Field(default_factory=list, description="Things we're inferring")
    risk_flags: List[str] = Field(default_factory=list, description="Approval triggers: large_blast, PII_export, etc.")

    @validator('kpis', pre=True, always=True)
    def default_kpis(cls, v):
        """If empty, add default KPI."""
        return v if v else ["placement_coverage_pct"]


# ============ AppSpec ============
class EntityField(BaseModel):
    """Single field in an entity."""
    name: str
    type: Literal["string", "int", "float", "bool", "string[]", "datetime"]
    required: bool = True


class Entity(BaseModel):
    """Business object: Person, Group, etc."""
    name: str
    fields: Dict[str, str]  # field_name: type (simplified for now)


class View(BaseModel):
    """UI view specification."""
    type: Literal["list", "detail", "calendar"]
    entity: str
    filters: Optional[List[str]] = None
    date_field: Optional[str] = None  # for calendar views


class WorkflowStep(BaseModel):
    """Single step in a workflow."""
    tool: str  # import_from_sheet, segment_audience, etc.
    input: Dict[str, Any]


class Workflow(BaseModel):
    """Multi-step process."""
    name: str
    steps: List[WorkflowStep]
    outputs: List[str]


class AppSpec(BaseModel):
    """Complete executable app specification."""
    app_name: str
    entities: List[Entity]
    views: List[View]
    workflows: List[Workflow]
    connectors: Dict[str, Any]  # {sheets: true, sms: "twilio", email: "mailgun"}
    policies: Dict[str, Any]  # {human_approval: true, max_blast: 200}

    @validator('workflows')
    def must_have_approval_gate(cls, v):
        """Every workflow must have exactly one approval_gate before any send/assign."""
        for wf in v:
            approval_count = sum(1 for step in wf.steps if step.tool == "approval_gate")
            if approval_count != 1:
                raise ValueError(f"Workflow '{wf.name}' must have exactly 1 approval_gate (found {approval_count})")
        return v


# ============ FeedbackSpec ============
class ChangeRule(BaseModel):
    """Single modification to an AppSpec."""
    replace: Optional[str] = None  # JSONPath to field
    set: Optional[str] = None
    value: Any


class FeedbackSpec(BaseModel):
    """User-requested changes to a plan."""
    change_rules: List[ChangeRule]
    reason: str


# ============ API Request/Response Models ============
class InterpretRequest(BaseModel):
    ask: str
    context: Optional[Dict[str, Any]] = None


class InterpretResponse(BaseModel):
    goalspec: GoalSpec
    error: Optional[Dict[str, str]] = None


class CompileRequest(BaseModel):
    goal: GoalSpec
    feedback: Optional[FeedbackSpec] = None


class CompileResponse(BaseModel):
    appspec: Optional[AppSpec] = None
    plan_diff: List[str] = Field(default_factory=list)
    error: Optional[Dict[str, str]] = None
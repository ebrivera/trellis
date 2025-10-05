from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal

# ============ GoalSpec ============
class GoalSpec(BaseModel):
    """Normalized, structured representation of what the user wants."""
    objective: str = Field(..., description="Single-sentence goal")  # The main goal in a single sentence
    constraints: List[str] = Field(default_factory=list, description="Hard rules: no X, only Y, etc.")  # Non-negotiable limitations
    kpis: List[str] = Field(default_factory=list, description="Metrics to track success")  # Key metrics used to evaluate success
    inputs_required: List[str] = Field(default_factory=list, description="Data sources needed: people_sheet, groups_sheet, etc.")  # Required input data sources
    assumptions: List[str] = Field(default_factory=list, description="Things we're inferring")  # Assumptions made in the goal
    risk_flags: List[str] = Field(default_factory=list, description="Approval triggers: large_blast, PII_export, etc.")  # Potential risks or special attention points

    @validator('kpis', pre=True, always=True)
    def default_kpis(cls, v):
        """If empty, add default KPI."""
        return v if v else ["placement_coverage_pct"]  # Ensures at least one KPI exists


# ============ AppSpec ============

class Entity(BaseModel):
    """Business object: Person, Group, etc."""
    name: str  # Name of the entity type (e.g., Person, Group)
    fields: Dict[str, str]  # Field definitions for the entity: field_name -> type


class View(BaseModel):
    """UI view specification."""
    type: Literal["list", "detail", "calendar"]  # The type of UI view
    entity: str  # Which entity this view represents
    filters: Optional[List[str]] = None  # Optional filters for the view
    date_field: Optional[str] = None  # Used for calendar-type views to determine date


class WorkflowStep(BaseModel):
    """Single step in a workflow."""
    tool: str  # Name of the tool or action to execute (e.g., import_from_sheet)
    input: Dict[str, Any]  # Input parameters for that tool


class Workflow(BaseModel):
    """Multi-step process."""
    name: str  # Workflow name
    steps: List[WorkflowStep]  # Ordered list of steps in this workflow
    outputs: List[str]  # Outputs produced after workflow completion


class AppSpec(BaseModel):
    """Complete executable app specification."""
    app_name: str  # Name of the app
    entities: List[Entity]  # Entities used in the app (e.g., People, Groups)
    views: List[View]  # UI views associated with the app
    workflows: List[Workflow]  # Workflows that define the app logic
    connectors: Dict[str, Any]  # External service connections (e.g., email, SMS, sheets)
    policies: Dict[str, Any]  # Application-level constraints or rules

    @validator('workflows')
    def must_have_approval_gate(cls, v):
        """Every workflow must have exactly one approval_gate before any send/assign."""
        for wf in v:
            approval_count = sum(1 for step in wf.steps if step.tool == "approval_gate")  # Count approval steps
            if approval_count != 1:
                raise ValueError(f"Workflow '{wf.name}' must have exactly 1 approval_gate (found {approval_count})")
        return v  # Return validated workflows


# ============ FeedbackSpec ============
class ChangeRule(BaseModel):
    """Single modification to an AppSpec."""
    replace: Optional[str] = None  # JSONPath to field to replace
    set: Optional[str] = None  # Name of the field to set
    value: Any  # New value to assign


class FeedbackSpec(BaseModel):
    """User-requested changes to a plan."""
    change_rules: List[ChangeRule]  # List of modifications to apply
    reason: str  # User’s reasoning behind requested changes


# ============ API Request/Response Models ============
class InterpretRequest(BaseModel):
    """Request schema for interpreting a user's input."""
    ask: str  # User's raw question or prompt
    context: Optional[Dict[str, Any]] = None  # Optional context data for interpretation


class InterpretResponse(BaseModel):
    """Response schema for interpretation step."""
    goalspec: GoalSpec  # Structured goal derived from the user's input
    error: Optional[Dict[str, str]] = None  # Error info if interpretation failed


class CompileRequest(BaseModel):
    """Request schema for compiling an app from a goal."""
    goal: GoalSpec  # The interpreted goal to compile
    feedback: Optional[FeedbackSpec] = None  # Optional feedback modifications


class CompileResponse(BaseModel):
    """Response schema after compiling the goal into an app."""
    appspec: Optional[AppSpec] = None  # The resulting executable app spec
    plan_diff: List[str] = Field(default_factory=list)  # Differences or changes applied
    error: Optional[Dict[str, str]] = None  # Error info if compilation failed

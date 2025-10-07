from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TemplateName(str, Enum):
    matching = "matching"
    monitoring = "monitoring"
    analysis = "analysis"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class WorkflowStatus(str, Enum):
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"
    failed = "failed"


class NotificationTemplate(BaseModel):
    to: Literal["source", "target", "admin"]
    channel: Literal["sms", "email"]
    message: str


class WorkflowParams(BaseModel):
    source_file: str = Field(default="volunteers.csv", alias="sourceFile")
    target_file: Optional[str] = Field(default=None, alias="targetFile")
    filter_rules: Optional[Dict[str, Any]] = Field(default=None, alias="filterRules")
    match_strategy: Optional[Literal["capacity_balanced", "interest_overlap", "proximity"]] = Field(
        default=None, alias="matchStrategy"
    )
    notifications: List[NotificationTemplate] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class MatchingAssignment(BaseModel):
    source_id: str = Field(alias="sourceId")
    source_name: str = Field(alias="sourceName")
    target_id: str = Field(alias="targetId")
    target_name: str = Field(alias="targetName")
    match_score: float = Field(alias="matchScore")
    match_reason: str = Field(alias="matchReason")

    model_config = ConfigDict(populate_by_name=True)


class UnmatchedItem(BaseModel):
    id: str
    name: str
    reason: str


class MatchingPreview(BaseModel):
    assignments: List[MatchingAssignment]
    unmatched: List[UnmatchedItem]
    capacity_warnings: List[str] = Field(default_factory=list, alias="capacityWarnings")

    model_config = ConfigDict(populate_by_name=True)


class FlaggedItem(BaseModel):
    id: str
    name: str
    last_contact: Optional[str] = Field(default=None, alias="lastContact")
    days_since: int = Field(alias="daysSince")
    phone: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class MonitoringPreview(BaseModel):
    flagged_items: List[FlaggedItem] = Field(alias="flaggedItems")
    alert_recipients: List[str] = Field(alias="alertRecipients")
    condition: str

    model_config = ConfigDict(populate_by_name=True)


class AnalysisDimension(BaseModel):
    name: str
    current: float
    goal: Optional[float] = None
    progress: Optional[float] = None
    trend: Literal["up", "down", "stable"]


class LapsedItem(BaseModel):
    id: str
    name: str
    last_date: str = Field(alias="lastDate")
    days_since: int = Field(alias="daysSince")
    lifetime_total: Optional[float] = Field(default=None, alias="lifetimeTotal")

    model_config = ConfigDict(populate_by_name=True)


class AnalysisPreview(BaseModel):
    dimensions: List[AnalysisDimension]
    lapsed_items: List[LapsedItem] = Field(alias="lapsedItems")
    total_analyzed: int = Field(alias="totalAnalyzed")

    model_config = ConfigDict(populate_by_name=True)


TemplatePreview = Union[MatchingPreview, MonitoringPreview, AnalysisPreview]


class ResultAction(BaseModel):
    type: Literal["assignment", "notification", "calculation"]
    count: int
    description: str
    details: Optional[Dict[str, Any]] = None


class WorkflowResult(BaseModel):
    id: str
    template: TemplateName
    status: Literal["completed", "failed"]
    summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    actions: List[ResultAction] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.utcnow, alias="completedAt")

    model_config = ConfigDict(
        populate_by_name=True, json_encoders={datetime: lambda value: value.isoformat()}
    )


class OperationContext(BaseModel):
    user_id: Optional[str] = Field(default=None, alias="userId")
    request_id: Optional[str] = Field(default=None, alias="requestId")
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ApprovalGate(BaseModel):
    id: str
    workflow_id: str = Field(alias="workflowId")
    template: TemplateName
    status: ApprovalStatus = ApprovalStatus.pending
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    decided_at: Optional[datetime] = Field(default=None, alias="decidedAt")
    decision_reason: Optional[str] = Field(default=None, alias="decisionReason")
    params: WorkflowParams
    preview: TemplatePreview
    metrics: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[OperationContext] = None

    model_config = ConfigDict(
        populate_by_name=True, json_encoders={datetime: lambda value: value.isoformat()}
    )


class WorkflowRun(BaseModel):
    id: str
    template: TemplateName
    status: WorkflowStatus
    request: Optional[str] = None
    params: WorkflowParams
    approval_id: Optional[str] = Field(default=None, alias="approvalId")
    context: Optional[OperationContext] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    result: Optional[WorkflowResult] = None

    model_config = ConfigDict(
        populate_by_name=True, json_encoders={datetime: lambda value: value.isoformat()}
    )


class OrchestrateRequest(BaseModel):
    request: Optional[str] = None
    template: Optional[TemplateName] = None
    params: Optional[WorkflowParams] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateResponse(BaseModel):
    workflow_id: str = Field(alias="workflowId")
    approval_id: str = Field(alias="approvalId")
    status: WorkflowStatus
    template: TemplateName
    params: WorkflowParams
    preview: TemplatePreview
    metrics: Dict[str, Any] = Field(default_factory=dict)
    message: str
    received_at: datetime = Field(default_factory=datetime.utcnow, alias="receivedAt")

    model_config = ConfigDict(
        populate_by_name=True, json_encoders={datetime: lambda value: value.isoformat()}
    )


class ApprovalLookupParams(BaseModel):
    id: str

    model_config = ConfigDict(str_strip_whitespace=True)


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reason: Optional[str] = None


class ApprovalDecisionPayload(ApprovalDecisionRequest):
    id: str


class ApprovalResponse(BaseModel):
    workflow: WorkflowRun
    gate: ApprovalGate

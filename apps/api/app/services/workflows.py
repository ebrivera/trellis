from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple
from uuid import uuid4

from ..errors import ApplicationError
from ..schemas import (
    AnalysisDimension,
    AnalysisPreview,
    ApprovalDecisionPayload,
    ApprovalLookupParams,
    ApprovalResponse,
    ApprovalGate,
    ApprovalStatus,
    FlaggedItem,
    LapsedItem,
    MatchingAssignment,
    MatchingPreview,
    MonitoringPreview,
    NotificationTemplate,
    OperationContext,
    OrchestrateRequest,
    OrchestrateResponse,
    ResultAction,
    TemplateName,
    TemplatePreview,
    UnmatchedItem,
    WorkflowParams,
    WorkflowResult,
    WorkflowRun,
    WorkflowStatus,
)


@dataclass
class WorkflowRecord:
    run: WorkflowRun
    gate: ApprovalGate
    proposed_result: WorkflowResult


_WORKFLOW_STATE: Dict[str, WorkflowRecord] = {}
_APPROVAL_INDEX: Dict[str, str] = {}


async def create_workflow_run(
    request: OrchestrateRequest,
    context: OperationContext | None = None,
) -> OrchestrateResponse:
    template = request.template or TemplateName.matching
    params = (request.params or _default_params(template)).model_copy(deep=True)

    workflow_id = str(uuid4())
    approval_id = str(uuid4())

    preview, metrics, proposed_result = _generate_preview_and_result(template, params)

    gate = ApprovalGate(
        id=approval_id,
        workflow_id=workflow_id,
        template=template,
        params=params.model_copy(deep=True),
        preview=preview,
        metrics=metrics,
        context=context,
    )

    run = WorkflowRun(
        id=workflow_id,
        template=template,
        status=WorkflowStatus.awaiting_approval,
        request=request.request,
        params=params.model_copy(deep=True),
        approval_id=approval_id,
        context=context,
        metadata=request.metadata,
    )

    record = WorkflowRecord(run=run, gate=gate, proposed_result=proposed_result)
    _WORKFLOW_STATE[workflow_id] = record
    _APPROVAL_INDEX[approval_id] = workflow_id

    return OrchestrateResponse(
        workflow_id=workflow_id,
        approval_id=approval_id,
        status=run.status,
        template=template,
        params=params,
        preview=preview,
        metrics=metrics,
        message="Workflow queued and awaiting approval.",
    )


async def fetch_approval_gate(
    params: ApprovalLookupParams,
    context: OperationContext | None = None,
) -> ApprovalResponse:
    record = _get_record_by_approval_id(params.id)
    return ApprovalResponse(workflow=record.run, gate=record.gate)


async def decide_approval_gate(
    payload: ApprovalDecisionPayload,
    context: OperationContext | None = None,
) -> ApprovalResponse:
    record = _get_record_by_approval_id(payload.id)

    if record.gate.status != ApprovalStatus.pending:
        raise ApplicationError(
            "Approval already decided",
            status_code=409,
            code="APPROVAL_FINAL",
        )

    if payload.decision == "reject" and not payload.reason:
        raise ApplicationError(
            "Rejection requires a reason",
            status_code=400,
            code="MISSING_REASON",
        )

    now = datetime.utcnow()

    if payload.decision == "approve":
        completed_result = record.proposed_result.model_copy(update={"completed_at": now})
        gate = record.gate.model_copy(
            update={
                "status": ApprovalStatus.approved,
                "decided_at": now,
                "decision_reason": payload.reason,
            }
        )
        run = record.run.model_copy(
            update={
                "status": WorkflowStatus.completed,
                "updated_at": now,
                "result": completed_result,
            }
        )
        record.proposed_result = completed_result
    else:
        gate = record.gate.model_copy(
            update={
                "status": ApprovalStatus.rejected,
                "decided_at": now,
                "decision_reason": payload.reason,
            }
        )
        run = record.run.model_copy(
            update={
                "status": WorkflowStatus.rejected,
                "updated_at": now,
                "result": None,
            }
        )

    record.gate = gate
    record.run = run
    _WORKFLOW_STATE[run.id] = record
    _APPROVAL_INDEX[gate.id] = run.id

    return ApprovalResponse(workflow=record.run, gate=record.gate)


def _get_record_by_approval_id(approval_id: str) -> WorkflowRecord:
    workflow_id = _APPROVAL_INDEX.get(approval_id)
    if not workflow_id:
        raise ApplicationError(
            "Approval gate not found",
            status_code=404,
            code="APPROVAL_NOT_FOUND",
        )

    record = _WORKFLOW_STATE.get(workflow_id)
    if not record:
        raise ApplicationError(
            "Workflow run missing for approval gate",
            status_code=500,
            code="WORKFLOW_NOT_FOUND",
        )
    return record


def _default_params(template: TemplateName) -> WorkflowParams:
    if template == TemplateName.monitoring:
        return WorkflowParams(
            sourceFile="visitors.csv",
            filterRules={"daysSinceLastContact": 14},
            notifications=[
                NotificationTemplate(
                    to="admin",
                    channel="email",
                    message="{{count}} visitors need follow-up: {{names}}",
                )
            ],
            alertRecipients=["pastor@trellis.church"],
            condition="visit_date older than 14 days with no follow-up",
        )
    if template == TemplateName.analysis:
        return WorkflowParams(
            sourceFile="gifts.csv",
            targetFile="initiatives.csv",
            notifications=[
                NotificationTemplate(
                    to="admin",
                    channel="email",
                    message="Giving dashboard ready for review.",
                )
            ],
            metrics=[
                {"name": "totalRaised", "formula": "SUM(amount) GROUP BY initiative"},
                {"name": "donorCount", "formula": "COUNT(DISTINCT donor_id)"},
            ],
        )

    # Default to matching template
    return WorkflowParams(
        sourceFile="volunteers.csv",
        targetFile="roles.csv",
        matchStrategy="capacity_balanced",
        notifications=[
            NotificationTemplate(
                to="source",
                channel="sms",
                message="You're assigned to {{targetName}} on Sundays.",
            ),
            NotificationTemplate(
                to="admin",
                channel="email",
                message="Assignments ready for {{count}} volunteers.",
            ),
        ],
    )


def _generate_preview_and_result(
    template: TemplateName,
    params: WorkflowParams,
) -> Tuple[TemplatePreview, Dict[str, float | int | str], WorkflowResult]:
    if template == TemplateName.monitoring:
        return _build_monitoring_preview(params)
    if template == TemplateName.analysis:
        return _build_analysis_preview(params)
    return _build_matching_preview(params)


def _build_matching_preview(
    params: WorkflowParams,
) -> Tuple[TemplatePreview, Dict[str, float | int | str], WorkflowResult]:
    assignments = [
        MatchingAssignment(
            sourceId="vol-001",
            sourceName="Alice Johnson",
            targetId="role-usher",
            targetName="Sunday Usher",
            matchScore=0.92,
            matchReason="Available Sundays and interests include hospitality",
        ),
        MatchingAssignment(
            sourceId="vol-002",
            sourceName="Ben Ramirez",
            targetId="role-kids",
            targetName="Kids Ministry",
            matchScore=0.88,
            matchReason="Background check complete, interests match 'kids'",
        ),
        MatchingAssignment(
            sourceId="vol-003",
            sourceName="Carla Nguyen",
            targetId="role-worship",
            targetName="Worship Team",
            matchScore=0.85,
            matchReason="Plays guitar and available Thursdays rehearsals",
        ),
    ]

    unmatched = [
        UnmatchedItem(id="vol-010", name="David Lee", reason="No Sunday availability"),
        UnmatchedItem(id="vol-011", name="Emily Park", reason="All preferred roles at capacity"),
    ]

    preview = MatchingPreview(
        assignments=assignments,
        unmatched=unmatched,
        capacityWarnings=["Youth Leader currently at 3/3 capacity"],
    )

    metrics: Dict[str, float | int | str] = {
        "assignments": len(assignments),
        "unmatched": len(unmatched),
        "fillRate": "90%",
    }

    result = WorkflowResult(
        id=str(uuid4()),
        template=TemplateName.matching,
        status="completed",
        summary=f"Prepared {len(assignments)} volunteer-to-role assignments.",
        metrics={"assignments": len(assignments), "notifications": 2, "fillRate": "90%"},
        actions=[
            ResultAction(
                type="assignment",
                count=len(assignments),
                description="Create assignments in database after approval",
                details={"targetFile": params.target_file},
            ),
            ResultAction(
                type="notification",
                count=len(params.notifications or []),
                description="Send notifications defined in workflow parameters",
            ),
        ],
    )

    return preview, metrics, result


def _build_monitoring_preview(
    params: WorkflowParams,
) -> Tuple[TemplatePreview, Dict[str, float | int | str], WorkflowResult]:
    flagged_items = [
        FlaggedItem(
            id="visitor-001",
            name="Sam Lee",
            lastContact=None,
            daysSince=18,
            email="sam.lee@example.com",
            phone="+15555550001",
        ),
        FlaggedItem(
            id="visitor-005",
            name="Priya Patel",
            lastContact="2024-09-12",
            daysSince=21,
            email="priya.patel@example.com",
        ),
    ]

    alert_recipients = getattr(params, "alertRecipients", ["pastor@trellis.church"])

    preview = MonitoringPreview(
        flaggedItems=flagged_items,
        alertRecipients=alert_recipients,
        condition=getattr(
            params,
            "condition",
            "Visited more than 14 days ago without follow-up",
        ),
    )

    metrics: Dict[str, float | int | str] = {
        "flagged": len(flagged_items),
        "avgDaysSince": 19,
    }

    result = WorkflowResult(
        id=str(uuid4()),
        template=TemplateName.monitoring,
        status="completed",
        summary=f"Identified {len(flagged_items)} visitors requiring follow-up.",
        metrics={"flagged": len(flagged_items), "notifications": 1},
        actions=[
            ResultAction(
                type="notification",
                count=1,
                description="Send alert email to oversight team",
                details={"recipients": alert_recipients},
            )
        ],
    )

    return preview, metrics, result


def _build_analysis_preview(
    params: WorkflowParams,
) -> Tuple[TemplatePreview, Dict[str, float | int | str], WorkflowResult]:
    dimensions = [
        AnalysisDimension(name="Building Fund", current=45000, goal=100000, progress=0.45, trend="up"),
        AnalysisDimension(name="Youth Outreach", current=22000, goal=30000, progress=0.73, trend="stable"),
        AnalysisDimension(name="Community Care", current=18000, goal=25000, progress=0.72, trend="down"),
    ]

    lapsed_items = [
        LapsedItem(
            id="donor-014",
            name="Jordan Smith",
            lastDate="2024-07-01",
            daysSince=96,
            lifetimeTotal=5400,
        ),
        LapsedItem(
            id="donor-022",
            name="Mia Hernandez",
            lastDate="2024-06-15",
            daysSince=112,
            lifetimeTotal=3200,
        ),
    ]

    preview = AnalysisPreview(
        dimensions=dimensions,
        lapsedItems=lapsed_items,
        totalAnalyzed=200,
    )

    metrics: Dict[str, float | int | str] = {
        "initiatives": len(dimensions),
        "lapsedDonors": len(lapsed_items),
    }

    result = WorkflowResult(
        id=str(uuid4()),
        template=TemplateName.analysis,
        status="completed",
        summary="Generated giving trends dashboard across initiatives.",
        metrics={"initiatives": len(dimensions), "lapsedDonors": len(lapsed_items)},
        actions=[
            ResultAction(
                type="calculation",
                count=len(dimensions),
                description="Calculated metrics for each initiative",
            ),
            ResultAction(
                type="notification",
                count=len(params.notifications or []),
                description="Notify admin that analysis is ready",
            ),
        ],
    )

    return preview, metrics, result

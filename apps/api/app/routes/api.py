from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, Header, status

from .. import audit
from ..errors import ApplicationError
from ..schemas import (
    ApprovalLookupParams,
    ApprovalResponse,
    OperationContext,
    OrchestrateRequest,
    OrchestrateResponse,
    TemplateName,
    WorkflowPayload,
)

router = APIRouter()

_START_TIME = time.perf_counter()


def _current_uptime() -> float:
    return time.perf_counter() - _START_TIME


@router.get("/health")
async def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "uptime": _current_uptime(),
        "timestamp": datetime.utcnow().isoformat(),
    }


async def get_operation_context(
    x_user_id: str | None = Header(default=None, alias="x-user-id"),
    x_request_id: str | None = Header(default=None, alias="x-request-id"),
) -> OperationContext:
    return OperationContext(
        user_id=x_user_id,
        request_id=x_request_id,
        source="api",
    )


async def _orchestrate_workflow(
    payload: OrchestrateRequest,
    context: OperationContext | None = None,
) -> OrchestrateResponse:
    template = payload.template or TemplateName.matching
    workflow = WorkflowPayload(template=template, params=payload.params or {})

    return OrchestrateResponse(
        status="pending",
        workflow=workflow,
        message="Workflow queued for approval. Implement executor to continue.",
        received_at=datetime.utcnow(),
    )


@router.post(
    "/orchestrate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=OrchestrateResponse,
    response_model_by_alias=True,
)
async def orchestrate_workflow(
    payload: OrchestrateRequest,
    base_context: OperationContext = Depends(get_operation_context),
) -> OrchestrateResponse:
    context = OperationContext(
        user_id=base_context.user_id,
        request_id=base_context.request_id,
        source=base_context.source,
        metadata=payload.metadata or {},
    )

    return await audit.audit_call("orchestrate_workflow", _orchestrate_workflow, payload, context)


async def _fetch_approval_gate(
    params: ApprovalLookupParams,
    _context: OperationContext | None = None,
) -> ApprovalResponse:
    if not params.id:
        raise ApplicationError(
            "Approval identifier is required",
            status_code=400,
            code="MISSING_ID",
        )

    return ApprovalResponse(
        id=params.id,
        status="pending",
        changes=[],
        next_actions=[
            {"label": "Approve", "href": f"/approval/{params.id}/approve"},
            {"label": "Reject", "href": f"/approval/{params.id}/reject"},
        ],
    )


@router.get(
    "/approval/{approval_id}",
    response_model=ApprovalResponse,
    response_model_by_alias=True,
)
async def get_approval_gate(
    approval_id: str,
    context: OperationContext = Depends(get_operation_context),
) -> ApprovalResponse:
    params = ApprovalLookupParams(id=approval_id)
    return await audit.audit_call("fetch_approval_gate", _fetch_approval_gate, params, context)

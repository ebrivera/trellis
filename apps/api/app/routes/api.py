from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, Header, status

from .. import audit
from ..schemas import (
    ApprovalDecisionPayload,
    ApprovalDecisionRequest,
    ApprovalLookupParams,
    ApprovalResponse,
    OperationContext,
    OrchestrateRequest,
    OrchestrateResponse,
)
from ..services.workflows import (
    create_workflow_run,
    decide_approval_gate as decide_gate,
    fetch_approval_gate as fetch_gate,
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

    return await audit.audit_call("orchestrate_workflow", create_workflow_run, payload, context)


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
    return await audit.audit_call("fetch_approval_gate", fetch_gate, params, context)


@router.post(
    "/approval/{approval_id}/decide",
    response_model=ApprovalResponse,
    response_model_by_alias=True,
)
async def decide_approval_gate(
    approval_id: str,
    request: ApprovalDecisionRequest,
    context: OperationContext = Depends(get_operation_context),
) -> ApprovalResponse:
    payload = ApprovalDecisionPayload(id=approval_id, decision=request.decision, reason=request.reason)
    return await audit.audit_call("decide_approval_gate", decide_gate, payload, context)

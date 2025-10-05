from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class TemplateName(str, Enum):
    matching = "matching"
    monitoring = "monitoring"
    analysis = "analysis"


class WorkflowPayload(BaseModel):
    template: TemplateName
    params: Dict[str, Any] = Field(default_factory=dict)


class OrchestrateRequest(BaseModel):
    request: str | None = None
    template: TemplateName | None = None
    params: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OperationContext(BaseModel):
    user_id: str | None = Field(default=None, alias="userId")
    request_id: str | None = Field(default=None, alias="requestId")
    source: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class OrchestrateResponse(BaseModel):
    status: Literal["pending"] = "pending"
    workflow: WorkflowPayload
    message: str
    received_at: datetime = Field(default_factory=datetime.utcnow, alias="receivedAt")

    model_config = ConfigDict(populate_by_name=True, json_encoders={datetime: lambda value: value.isoformat()})


class ApprovalLookupParams(BaseModel):
    id: str

    model_config = ConfigDict(str_strip_whitespace=True)


class ApprovalResponse(BaseModel):
    id: str
    status: Literal["pending", "approved", "rejected"]
    changes: list[Dict[str, Any]] = Field(default_factory=list)
    next_actions: list[Dict[str, str]] = Field(default_factory=list, alias="nextActions")

    model_config = ConfigDict(populate_by_name=True)

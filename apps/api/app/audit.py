from __future__ import annotations

import inspect
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, TypeVar
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from .schemas import OperationContext

logger = logging.getLogger("trellis.audit")

TResult = TypeVar("TResult")
TParams = TypeVar("TParams")


def _to_serializable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()  # type: ignore[attr-defined]
    return jsonable_encoder(value)


async def _ensure_awaitable(value: Awaitable[TResult] | TResult) -> TResult:
    if inspect.isawaitable(value):
        return await value  # type: ignore[return-value]
    return value  # type: ignore[return-value]


async def audit_call(
    function_name: str,
    fn: Callable[[TParams, OperationContext | None], Awaitable[TResult] | TResult],
    params: TParams,
    context: OperationContext | None = None,
) -> TResult:
    entry_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat()
    context_payload = _to_serializable(context) if context else None
    params_payload = _to_serializable(params)

    try:
        result = await _ensure_awaitable(fn(params, context))
        logger.info(
            "[audit] success",
            extra={
                "id": entry_id,
                "timestamp": timestamp,
                "function": function_name,
                "params": params_payload,
                "result": _to_serializable(result),
                "context": context_payload,
            },
        )
        return result
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "[audit] failure",
            extra={
                "id": entry_id,
                "timestamp": timestamp,
                "function": function_name,
                "params": params_payload,
                "context": context_payload,
                "error": str(exc),
            },
        )
        raise

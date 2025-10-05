from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger("trellis.errors")


class ApplicationError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


async def application_error_handler(_request: Request, exc: ApplicationError) -> JSONResponse:
    logger.error(
        "application error",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)

    logger.exception("unhandled exception", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "Unexpected error",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

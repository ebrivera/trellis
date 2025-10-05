from __future__ import annotations

import logging

from fastapi import FastAPI

from .errors import register_exception_handlers
from .routes.api import router as api_router


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(title="Trellis API", version="0.1.0")
    app.include_router(api_router)
    register_exception_handlers(app)
    return app


app = create_app()

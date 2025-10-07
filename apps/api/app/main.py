from __future__ import annotations

import logging

from fastapi import FastAPI

from .config import get_settings
from .errors import register_exception_handlers
from .routes import router as api_router


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(api_router)
    register_exception_handlers(app)
    app.state.settings = settings

    return app


app = create_app()

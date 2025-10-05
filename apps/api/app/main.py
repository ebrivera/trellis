from __future__ import annotations

import logging

from fastapi import FastAPI

from .config import get_settings
from .errors import register_exception_handlers
from .routes.api import router as api_router
from .services.supabase import build_supabase_client


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    app = FastAPI(title="Trellis API", version="0.1.0")
    app.include_router(api_router)
    register_exception_handlers(app)
    app.state.settings = settings
    app.state.supabase = build_supabase_client(settings)

    if app.state.supabase is not None:
        logging.getLogger("trellis.supabase").info("Supabase client ready: %s", settings.supabase_url)

    return app


app = create_app()

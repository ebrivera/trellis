from __future__ import annotations

import logging
from typing import Optional

from supabase import Client, create_client

from ..config import Settings

logger = logging.getLogger("trellis.supabase")


def build_supabase_client(settings: Settings) -> Optional[Client]:
    """Create a Supabase client when credentials are available."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning(
            "Supabase credentials not provided; proceeding without an authenticated client."
        )
        return None

    try:
        return create_client(settings.supabase_url, settings.supabase_service_role_key)
    except Exception:  # noqa: BLE001 - surface original failure for visibility
        logger.exception("Failed to initialise Supabase client")
        return None

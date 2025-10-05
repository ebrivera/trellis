from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass
class Settings:
    node_env: str = os.getenv("NODE_ENV", "development")
    port: int = int(os.getenv("PORT", "4000"))
    database_url: str = os.getenv("DATABASE_URL", "")
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str | None = os.getenv("SUPABASE_ANON_KEY")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

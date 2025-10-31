from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Trellis API"
    app_version: str = "0.1.0"


def get_settings() -> Settings:
    return Settings()

"""Application configuration.

All secrets come from the environment. LLM integration is OFF by default and the
entire core demo runs without any API key or network access.
"""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Environment-driven settings (no secrets committed)."""

    def __init__(self) -> None:
        self.app_name: str = "SpecterRed X"
        self.schema_version: int = 1
        # Database lives next to the backend package so history survives restarts.
        default_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "specterred.db")
        self.database_url: str = os.getenv("SPECTERRED_DB_URL", f"sqlite:///{default_db}")

        # CORS: only the local dev frontend origin by default.
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv(
                "SPECTERRED_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if o.strip()
        ]

        # Optional LLM narrative assist. Empty => deterministic policy mode only.
        self.llm_base_url: str = os.getenv("LLM_BASE_URL", "")
        self.llm_api_key: str = os.getenv("LLM_API_KEY", "")
        self.llm_model: str = os.getenv("LLM_MODEL", "")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()

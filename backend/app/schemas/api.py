"""Pydantic v2 request/response schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1, max_length=32)
    config: dict[str, str] | None = None
    seed: int = Field(default=1337, ge=0, le=2**31 - 1)


class ReplayRequest(BaseModel):
    control_changes: dict[str, str] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    comparison_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    schema_version: int
    llm_enabled: bool
    llm_mode: str
    mitre_available: bool
    webgl_note: str

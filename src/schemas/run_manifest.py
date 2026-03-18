"""Schema for a run manifest."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunIdentifier(BaseModel):
    type: str
    value: str
    exchange: str | None = None


class RunManifest(BaseModel):
    run_id: str
    workspace_root: str
    workspace_revision: str
    status: str
    identifier: RunIdentifier
    report_type: str
    started_at: datetime
    completed_at: datetime | None = None
    schema_version: str
    tool_versions: dict[str, str] = Field(default_factory=dict)
    retries_of: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)

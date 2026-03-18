"""Gateway request and response contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .provenance import ProvenanceRecord


class RequestContext(BaseModel):
    request_id: str
    trace_id: str
    requester: str
    team: str
    purpose: str
    requested_at: datetime


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ToolResponseEnvelope(BaseModel):
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    errors: list[ErrorEnvelope] = Field(default_factory=list)

"""Schema for narrative claims."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NarrativeClaim(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str
    entity: str | None = None
    time_scope: str | None = None
    source_ids: list[str]
    evidence_spans: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

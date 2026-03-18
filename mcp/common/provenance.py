"""Provenance models shared by MCP tools."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    source_id: str
    source_type: str
    source_system: str
    retrieved_at: datetime
    as_of_datetime: datetime | None = None
    license_scope: str
    confidence: float = Field(ge=0.0, le=1.0)
    content_hash: str


class CitationSpan(BaseModel):
    claim_id: str | None = None
    document_id: str
    page_or_section: str
    extracted_text: str
    as_of_datetime: datetime | None = None
    parser_version: str
    confidence: float = Field(ge=0.0, le=1.0)

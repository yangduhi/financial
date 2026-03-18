"""Schema for a source document."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SourceDocument(BaseModel):
    source_id: str
    document_id: str
    issuer: str
    document_type: str
    published_at: datetime | None = None
    fiscal_period: str | None = None
    language: str | None = None
    uri: str | None = None
    license_scope: str
    content_hash: str

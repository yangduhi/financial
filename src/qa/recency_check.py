"""Recency QA scaffold."""

from __future__ import annotations

from datetime import datetime


def is_primary_document_current(published_at: datetime, latest_seen: datetime) -> bool:
    return published_at >= latest_seen

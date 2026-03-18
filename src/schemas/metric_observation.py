"""Schema for normalized metric observations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MetricObservation(BaseModel):
    metric_name: str
    metric_value: Decimal
    currency: str | None = None
    unit: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    as_of_datetime: datetime | None = None
    share_basis: str | None = None
    source_id: str
    extraction_method: str
    confidence: float = Field(ge=0.0, le=1.0)
    original_label: str | None = None

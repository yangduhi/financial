"""Helpers for run identifiers and status management."""

import datetime as dt

RUN_STATUS_ORDER = [
    "created",
    "ingesting",
    "parsed",
    "normalized",
    "derived",
    "reported",
    "qa_passed",
    "qa_failed",
    "failed"
]


def build_run_id(as_of_date: str, identifier_slug: str, report_type: str) -> str:
    timestamp = dt.datetime.now(dt.UTC).strftime("%H%M%SZ")
    return f"{as_of_date}_{identifier_slug}_{report_type}_{timestamp}"

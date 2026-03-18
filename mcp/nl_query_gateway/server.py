"""Intent-level MCP gateway for natural-language finance questions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.orchestration.intent_tools import (
    get_metric_trend,
    get_quarterly_metrics,
    get_recent_filings,
    get_source_evidence,
    resolve_entity,
)
from src.orchestration.nl_query_runner import run_query


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str


NL_QUERY_GATEWAY_TOOLS = [
    ToolDefinition("resolve_entity", "Resolve a company expression into a canonical identifier."),
    ToolDefinition("get_quarterly_metrics", "Return quarterly metric values and sources."),
    ToolDefinition("get_metric_trend", "Return structured trend data for a metric."),
    ToolDefinition("get_recent_filings", "Return recent filings or earnings documents."),
    ToolDefinition("get_source_evidence", "Return short grounded excerpts for a topic or metric."),
    ToolDefinition("answer_query", "Run the end-to-end natural-language query flow."),
]


def list_tools() -> list[ToolDefinition]:
    return NL_QUERY_GATEWAY_TOOLS


def resolve_entity_tool(**kwargs):
    return resolve_entity(**kwargs)


def get_quarterly_metrics_tool(**kwargs):
    return get_quarterly_metrics(**kwargs)


def get_metric_trend_tool(**kwargs):
    return get_metric_trend(**kwargs)


def get_recent_filings_tool(**kwargs):
    return get_recent_filings(**kwargs)


def get_source_evidence_tool(**kwargs):
    return get_source_evidence(**kwargs)


def answer_query(question: str, persist: bool = False):
    run_id = f"nl_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    return run_query(question, persist=persist, run_id=run_id)

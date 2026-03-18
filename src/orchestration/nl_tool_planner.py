"""Plan intent-level tool sequences for supported NL questions."""

from __future__ import annotations

from typing import Any


def plan_tools(parsed_intent: dict[str, Any]) -> dict[str, Any]:
    status = parsed_intent.get("status")
    if status != "OK":
        return {"status": "PLANNER_FAILURE", "tools": [], "reason": status}

    intent = parsed_intent["intent"]
    if intent == "metric_trend":
        return {
            "status": "OK",
            "tools": ["resolve_entity", "get_metric_trend"],
            "tool_budget": 2,
        }
    if intent == "metric_compare":
        return {
            "status": "OK",
            "tools": ["resolve_entity", "get_quarterly_metrics", "get_source_evidence"],
            "tool_budget": 3,
        }
    if intent == "filing_evidence":
        return {
            "status": "OK",
            "tools": ["resolve_entity", "get_recent_filings", "get_source_evidence"],
            "tool_budget": 3,
        }
    return {"status": "PLANNER_FAILURE", "tools": [], "reason": "UNSUPPORTED_INTENT"}

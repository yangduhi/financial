"""End-to-end runner for natural-language MCP practice queries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .intent_tools import (
    get_metric_trend,
    get_quarterly_metrics,
    get_recent_filings,
    get_source_evidence,
    resolve_entity,
)
from .nl_answer_generator import (
    generate_filing_evidence_answer,
    generate_metric_compare_answer,
    generate_metric_trend_answer,
)
from .nl_intent_parser import parse_intent
from .nl_query_normalizer import normalize_query
from .nl_run_artifacts import persist_query_run
from .nl_tool_planner import plan_tools


def run_query(query: str, persist: bool = False, run_id: str | None = None) -> dict[str, Any]:
    trace: dict[str, Any] = {"raw_query": query}

    normalized = normalize_query(query)
    trace["normalized_query"] = normalized

    parsed = parse_intent(normalized["normalized_query"], normalized.get("entity_hint"))
    trace["parsed_intent"] = parsed
    if parsed["status"] != "OK":
        result = {"status": parsed["status"], "trace": trace, "answer": None}
        if persist:
            run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            result["artifacts"] = persist_query_run(run_id, query, result)
        return result

    plan = plan_tools(parsed)
    trace["tool_plan"] = plan
    if plan["status"] != "OK":
        result = {"status": "PLANNER_FAILURE", "trace": trace, "answer": None}
        if persist:
            run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            result["artifacts"] = persist_query_run(run_id, query, result)
        return result

    entity = resolve_entity(parsed["entity_hint"] or query)
    trace["resolve_entity"] = entity
    if entity["status"] != "RESOLVED":
        result = {"status": entity["status"], "trace": trace, "answer": None}
        if persist:
            run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            result["artifacts"] = persist_query_run(run_id, query, result)
        return result

    identifier = entity["selected"]["identifier"]
    intent = parsed["intent"]

    if intent == "metric_trend":
        evidence_result = get_source_evidence(
            identifier=identifier,
            metric=parsed["metric"],
            topic=parsed.get("topic"),
            limit=1,
        )
        trend_result = get_metric_trend(
            identifier=identifier,
            metric=parsed["metric"],
            quarter_count=parsed["period"]["value"],
        )
        trace["get_metric_trend"] = {
            "status": trend_result["status"],
            "series_count": len(trend_result.get("series", [])),
        }
        answer = generate_metric_trend_answer(
            entity["selected"]["company_name"],
            parsed["metric"],
            trend_result,
            evidence_result=evidence_result,
        )
        result = {"status": trend_result["status"], "trace": trace, "answer": answer}
        if persist:
            run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            result["artifacts"] = persist_query_run(run_id, query, result)
        return result

    if intent == "metric_compare":
        metrics = (
            [parsed["metric"]]
            if parsed.get("metric")
            else ["revenue", "operating_income", "eps", "fcf"]
        )
        metrics_result = get_quarterly_metrics(
            identifier=identifier, metrics=metrics, quarter_count=2
        )
        evidence_result = get_source_evidence(
            identifier=identifier,
            metric=parsed.get("metric"),
            topic=parsed.get("topic"),
            limit=2,
        )
        trace["get_quarterly_metrics"] = {
            "status": metrics_result["status"],
            "period_count": len(metrics_result.get("periods", [])),
        }
        trace["get_source_evidence"] = {
            "status": evidence_result["status"],
            "evidence_count": len(evidence_result.get("evidence", [])),
        }
        answer = generate_metric_compare_answer(
            entity["selected"]["company_name"],
            metrics_result,
            metric=parsed.get("metric"),
            evidence_result=evidence_result,
        )
        result = {"status": metrics_result["status"], "trace": trace, "answer": answer}
        if persist:
            run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            result["artifacts"] = persist_query_run(run_id, query, result)
        return result

    if intent == "filing_evidence":
        filings_result = get_recent_filings(
            identifier=identifier,
            doc_types=["earnings_release", "earnings_call_transcript", "10-Q"],
            limit=3,
        )
        evidence_result = get_source_evidence(
            identifier=identifier,
            topic=parsed.get("topic"),
            metric=parsed.get("metric"),
            limit=3,
        )
        trace["get_recent_filings"] = {
            "status": filings_result["status"],
            "item_count": len(filings_result.get("items", [])),
        }
        trace["get_source_evidence"] = {
            "status": evidence_result["status"],
            "evidence_count": len(evidence_result.get("evidence", [])),
        }
        answer = generate_filing_evidence_answer(
            entity["selected"]["company_name"],
            parsed.get("topic"),
            filings_result,
            evidence_result,
        )
        result = {"status": evidence_result["status"], "trace": trace, "answer": answer}
        if persist:
            run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            result["artifacts"] = persist_query_run(run_id, query, result)
        return result

    result = {"status": "UNSUPPORTED_INTENT", "trace": trace, "answer": None}
    if persist:
        run_id = run_id or f"nl_query_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        result["artifacts"] = persist_query_run(run_id, query, result)
    return result

"""Persist natural-language query runs into run artifacts."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.schemas.run_manifest import RunIdentifier, RunManifest

from .config_loader import load_output_paths

ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _resolve_path(pattern: str, run_id: str) -> Path:
    relative = pattern.format(run_id=run_id)
    return ROOT / relative


def create_run_layout(run_id: str) -> dict[str, Path]:
    config = load_output_paths().get("paths", {})
    resolved = {key: _resolve_path(value, run_id) for key, value in config.items()}
    for key, path in resolved.items():
        if key.endswith("_dir") or key.endswith("_root"):
            path.mkdir(parents=True, exist_ok=True)
    return resolved


def build_source_map(query: str, result: dict[str, Any]) -> dict[str, Any]:
    trace = result.get("trace", {})
    return {
        "question": query,
        "answer": result.get("answer"),
        "status": result.get("status"),
        "parsed_intent": trace.get("parsed_intent", {}),
        "tool_plan": trace.get("tool_plan", {}),
        "entity": trace.get("resolve_entity", {}),
        "sources": {
            "trend_sources": (trace.get("get_metric_trend") or {}),
            "evidence_sources": (trace.get("get_source_evidence") or {}),
            "filing_sources": (trace.get("get_recent_filings") or {}),
        },
    }


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def build_qa_report(result: dict[str, Any]) -> dict[str, Any]:
    status = result.get("status")
    answer = result.get("answer")
    trace = result.get("trace", {})
    entity_status = (trace.get("resolve_entity") or {}).get("status")
    parsed_intent = trace.get("parsed_intent") or {}
    tool_plan = trace.get("tool_plan") or {}
    source_evidence = trace.get("get_source_evidence") or {}
    recent_filings = trace.get("get_recent_filings") or {}
    metric_trend = trace.get("get_metric_trend") or {}
    quarterly_metrics = trace.get("get_quarterly_metrics") or {}

    answer_present = bool(answer)
    tool_plan_present = bool(tool_plan.get("tools"))
    entity_resolved = entity_status == "RESOLVED"
    status_supported = status in {"OK", "PARTIAL", "INSUFFICIENT_EVIDENCE"}

    answer_text = answer or ""
    has_period_binding = (
        bool(re.search(r"\b20\d{2}Q[1-4]\b", answer_text)) or "최근 분기" in answer_text
    )
    has_source_or_limitation = any(token in answer_text for token in ["근거:", "제한:", "출처:"])
    has_uncertainty_when_needed = not (
        status == "INSUFFICIENT_EVIDENCE"
        and not any(token in answer_text for token in ["확보하지 못", "부족", "제한"])
    )
    evidence_request_respected = True
    if parsed_intent.get("intent") == "filing_evidence":
        evidence_request_respected = (
            bool(source_evidence.get("evidence_count", 0)) or status == "INSUFFICIENT_EVIDENCE"
        )

    execution_checks = [
        _check(
            "answer_present",
            answer_present,
            "answer text exists" if answer_present else "missing answer",
        ),
        _check(
            "tool_plan_present",
            tool_plan_present,
            "tool plan captured" if tool_plan_present else "missing tool plan",
        ),
        _check(
            "entity_resolved",
            entity_resolved,
            "entity resolved" if entity_resolved else f"entity status: {entity_status}",
        ),
        _check(
            "status_supported",
            status_supported,
            f"query status {status}" if status_supported else f"unsupported status {status}",
        ),
    ]

    grounding_checks = [
        _check(
            "period_binding_present",
            has_period_binding or parsed_intent.get("intent") == "filing_evidence",
            (
                "answer references fiscal period"
                if has_period_binding
                else "period tokens not found in answer"
            ),
        ),
        _check(
            "source_or_limitation_present",
            has_source_or_limitation,
            "answer includes source or limitation section"
            if has_source_or_limitation
            else "source/limitation section missing",
        ),
        _check(
            "uncertainty_handling",
            has_uncertainty_when_needed,
            "uncertainty wording present when evidence is insufficient"
            if has_uncertainty_when_needed
            else "missing uncertainty wording for insufficient evidence",
        ),
        _check(
            "evidence_request_respected",
            evidence_request_respected,
            "evidence request handled with evidence or explicit insufficiency"
            if evidence_request_respected
            else "evidence request missing support",
        ),
    ]

    artifact_checks = [
        _check(
            "trend_trace_present",
            bool(metric_trend) or parsed_intent.get("intent") != "metric_trend",
            "trend trace present" if bool(metric_trend) else "trend trace missing",
        ),
        _check(
            "compare_trace_present",
            bool(quarterly_metrics) or parsed_intent.get("intent") != "metric_compare",
            "compare trace present" if bool(quarterly_metrics) else "compare trace missing",
        ),
        _check(
            "filing_trace_present",
            bool(recent_filings) or parsed_intent.get("intent") != "filing_evidence",
            "filing trace present" if bool(recent_filings) else "filing trace missing",
        ),
    ]

    all_execution = all(item["passed"] for item in execution_checks)
    all_grounding = all(item["passed"] for item in grounding_checks)
    all_artifacts = all(item["passed"] for item in artifact_checks)

    if status == "OK" and all_execution and all_grounding and all_artifacts:
        qa_status = "pass"
    elif status in {"PARTIAL", "INSUFFICIENT_EVIDENCE"} and all_execution and all_artifacts:
        qa_status = "warn"
    else:
        qa_status = "fail"

    return {
        "status": qa_status,
        "query_status": status,
        "summary": {
            "execution_passed": all_execution,
            "grounding_passed": all_grounding,
            "artifact_passed": all_artifacts,
        },
        "execution_checks": execution_checks,
        "grounding_checks": grounding_checks,
        "artifact_checks": artifact_checks,
        "checked_at": datetime.now(UTC).isoformat(),
    }


def persist_query_run(
    run_id: str,
    query: str,
    result: dict[str, Any],
    report_type: str = "nl_query",
) -> dict[str, str]:
    paths = create_run_layout(run_id)
    trace = result.get("trace", {})
    entity = (trace.get("resolve_entity") or {}).get("selected") or {}

    input_payload = {"query": query, "report_type": report_type}
    source_map = build_source_map(query, result)
    qa_report = build_qa_report(result)

    manifest = RunManifest(
        run_id=run_id,
        workspace_root=str(ROOT),
        workspace_revision="nogit",
        status="qa_passed" if qa_report["status"] == "pass" else "qa_failed",
        identifier=RunIdentifier(
            type="ticker_exchange",
            value=entity.get("ticker", "UNKNOWN"),
            exchange=entity.get("exchange"),
        ),
        report_type=report_type,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        schema_version="1",
        inputs=input_payload,
    )

    _write_json(paths["input_file"], input_payload)
    _write_json(paths["manifest_file"], manifest.model_dump(mode="json"))
    _write_json(paths["source_map_file"], source_map)
    _write_json(paths["qa_report_file"], qa_report)
    _write_json(
        paths["failure_report_file"],
        {"status": qa_report["status"], "result": result.get("status")},
    )
    _write_json(paths["evidence_graph_file"], [{"question": query, "status": result.get("status")}])
    _write_text(paths["summary_file"], result.get("answer") or "")
    _write_text(paths["review_pack_file"], result.get("answer") or "")
    _write_json(paths["logs_dir"] / "tool_traces" / "trace.json", trace)

    return {key: str(path.relative_to(ROOT)) for key, path in paths.items()}

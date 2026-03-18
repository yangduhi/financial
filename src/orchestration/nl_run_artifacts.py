"""Persist natural-language query runs into run artifacts."""

from __future__ import annotations

import json
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
        "status": result.get("status"),
        "tool_plan": trace.get("tool_plan", {}),
        "entity": trace.get("resolve_entity", {}),
        "sources": {
            "trend_sources": (trace.get("get_metric_trend") or {}),
            "evidence_sources": (trace.get("get_source_evidence") or {}),
            "filing_sources": (trace.get("get_recent_filings") or {}),
        },
    }


def build_qa_report(result: dict[str, Any]) -> dict[str, Any]:
    status = result.get("status")
    answer = result.get("answer")
    trace = result.get("trace", {})
    entity_status = (trace.get("resolve_entity") or {}).get("status")

    checks = {
        "answer_present": bool(answer),
        "tool_plan_present": bool((trace.get("tool_plan") or {}).get("tools")),
        "entity_resolved": entity_status == "RESOLVED",
        "status_supported": status in {"OK", "PARTIAL", "INSUFFICIENT_EVIDENCE"},
    }

    if status == "OK" and all(checks.values()):
        qa_status = "pass"
    elif status in {"PARTIAL", "INSUFFICIENT_EVIDENCE"} and checks["answer_present"]:
        qa_status = "warn"
    else:
        qa_status = "fail"

    return {
        "status": qa_status,
        "query_status": status,
        "checks": checks,
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

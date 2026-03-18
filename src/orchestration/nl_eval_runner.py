"""Run and verify natural-language MCP evaluation questions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .nl_query_runner import run_query
from .run_context import build_run_id

ROOT = Path(__file__).resolve().parents[2]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _verify_question(question: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    passed = True
    reasons: list[str] = []

    if result["status"] not in question.get("expected_status", []):
        passed = False
        reasons.append(f"status mismatch: {result['status']}")

    actual_plan = (result.get("trace", {}).get("tool_plan") or {}).get("tools", [])
    if actual_plan != question.get("expected_tool_plan", []):
        passed = False
        reasons.append(f"tool plan mismatch: {actual_plan}")

    answer = result.get("answer") or ""
    for token in question.get("required_answer_substrings", []):
        if token not in answer:
            passed = False
            reasons.append(f"missing answer token: {token}")

    return {"passed": passed, "reasons": reasons}


def run_dataset(
    dataset_path: str = "evals/datasets/nl_questions_v1.json",
    report_basename: str = "nl_questions_v1",
) -> dict[str, Any]:
    dataset_file = ROOT / dataset_path
    dataset = json.loads(dataset_file.read_text(encoding="utf-8"))

    run_id = build_run_id("eval", report_basename, "nl_query")
    run_root = ROOT / "runs" / run_id
    traces_dir = run_root / "logs" / "tool_traces"
    failures_dir = run_root / "logs" / "failed_cases"
    artifacts_dir = run_root / "artifacts"
    _ensure_dir(traces_dir)
    _ensure_dir(failures_dir)
    _ensure_dir(artifacts_dir)

    answers: list[dict[str, Any]] = []
    verification_rows: list[dict[str, Any]] = []

    for item in dataset:
        result = run_query(item["question"])
        verification = _verify_question(item, result)
        trace_path = traces_dir / f"{item['id']}.json"
        _write_json(trace_path, result)

        answers.append(
            {
                "id": item["id"],
                "question": item["question"],
                "status": result["status"],
                "answer": result["answer"],
            }
        )
        verification_row = {
            "id": item["id"],
            "question": item["question"],
            "status": result["status"],
            "passed": verification["passed"],
            "reasons": verification["reasons"],
        }
        verification_rows.append(verification_row)

        if not verification["passed"]:
            _write_json(failures_dir / f"{item['id']}.json", verification_row)

    answers_path = ROOT / "evals" / "reports" / f"{report_basename}_answers.json"
    verification_path = ROOT / "evals" / "reports" / f"{report_basename}_verification.json"
    _write_json(answers_path, answers)
    _write_json(verification_path, verification_rows)

    pass_count = sum(1 for row in verification_rows if row["passed"])
    return {
        "run_id": run_id,
        "answers_path": str(answers_path.relative_to(ROOT)),
        "verification_path": str(verification_path.relative_to(ROOT)),
        "total": len(verification_rows),
        "passed": pass_count,
    }

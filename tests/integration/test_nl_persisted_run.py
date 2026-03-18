import json
from pathlib import Path

from src.orchestration.nl_query_runner import run_query


def test_run_query_persists_manifest_and_reports() -> None:
    result = run_query(
        "ANET의 최근 4분기 영업이익 변동을 알려줘.",
        persist=True,
        run_id="nl_query_test_artifacts",
    )
    artifacts = result.get("artifacts", {})
    assert "manifest_file" in artifacts
    assert "source_map_file" in artifacts
    assert "qa_report_file" in artifacts

    root = Path(__file__).resolve().parents[2]
    qa_report = json.loads((root / artifacts["qa_report_file"]).read_text(encoding="utf-8"))
    assert "execution_checks" in qa_report
    assert "grounding_checks" in qa_report
    assert "artifact_checks" in qa_report

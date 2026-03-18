from src.orchestration.nl_query_runner import run_query


def test_run_query_handles_metric_trend_question() -> None:
    result = run_query("ANET의 최근 4분기 영업이익 변동을 알려줘.")
    assert result["status"] in {"OK", "PARTIAL"}
    assert "영업이익" in (result["answer"] or "")


def test_run_query_handles_metric_compare_question() -> None:
    result = run_query("ANET의 최근 분기와 직전 분기 영업이익 비교해줘.")
    assert result["status"] in {"OK", "PARTIAL", "INSUFFICIENT_EVIDENCE"}
    assert "영업이익" in (result["answer"] or "")
    assert "근거" in (result["answer"] or "")


def test_run_query_handles_filing_evidence_question() -> None:
    result = run_query("ANET의 최근 실적 발표에서 가이던스 관련 핵심 문장만 알려줘.")
    assert result["status"] in {"OK", "INSUFFICIENT_EVIDENCE"}
    assert "근거" in (result["answer"] or "")

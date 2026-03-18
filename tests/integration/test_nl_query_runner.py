from src.orchestration.nl_query_runner import run_query


def test_run_query_handles_metric_trend_question() -> None:
    result = run_query("ANET의 최근 4분기 영업이익 변동을 알려줘.")
    assert result["status"] in {"OK", "PARTIAL"}
    assert "영업이익" in (result["answer"] or "")

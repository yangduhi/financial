from src.orchestration.run_context import build_run_id


def test_build_run_id_contains_key_parts() -> None:
    run_id = build_run_id("2026-03-18", "ANET_NYSE", "earnings_review")
    assert "2026-03-18" in run_id
    assert "ANET_NYSE" in run_id
    assert "earnings_review" in run_id

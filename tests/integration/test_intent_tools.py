from src.orchestration.intent_tools import get_metric_trend, resolve_entity


def test_resolve_entity_and_metric_trend_for_anet() -> None:
    entity = resolve_entity("ANET")
    assert entity["status"] == "RESOLVED"

    trend = get_metric_trend(
        entity["selected"]["identifier"], metric="operating_income", quarter_count=4
    )
    assert trend["status"] in {"OK", "PARTIAL"}
    assert len(trend["series"]) == 4

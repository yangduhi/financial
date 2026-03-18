from src.orchestration.nl_intent_parser import parse_intent
from src.orchestration.nl_query_normalizer import normalize_query


def test_normalize_query_extracts_entity_hint() -> None:
    normalized = normalize_query("ANET의 최근 4분기 영업이익 변동을 알려줘.")
    assert normalized["entity_hint"] == "ANET"


def test_parse_intent_detects_metric_trend() -> None:
    parsed = parse_intent("ANET의 최근 4분기 영업이익 변동을 알려줘.", entity_hint="ANET")
    assert parsed["status"] == "OK"
    assert parsed["intent"] == "metric_trend"
    assert parsed["metric"] == "operating_income"
    assert parsed["period"]["value"] == 4

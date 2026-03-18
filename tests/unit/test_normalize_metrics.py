from decimal import Decimal

from src.schemas.metric_observation import MetricObservation


def test_metric_observation_preserves_original_label() -> None:
    observation = MetricObservation(
        metric_name="revenue",
        metric_value=Decimal("100"),
        currency="USD",
        unit="million",
        source_id="doc-1",
        extraction_method="manual",
        confidence=0.8,
        original_label="Total revenue"
    )
    assert observation.original_label == "Total revenue"

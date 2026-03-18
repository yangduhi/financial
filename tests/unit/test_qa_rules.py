from decimal import Decimal

from src.qa.number_reconcile import exceeds_tolerance


def test_number_reconcile_detects_over_threshold() -> None:
    assert exceeds_tolerance(Decimal("10"), Decimal("13"), Decimal("2")) is True

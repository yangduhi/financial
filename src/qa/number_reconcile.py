"""Number reconciliation QA scaffold."""

from __future__ import annotations

from decimal import Decimal


def exceeds_tolerance(left: Decimal, right: Decimal, tolerance: Decimal) -> bool:
    return abs(left - right) > tolerance

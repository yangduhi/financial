"""Unit and basis QA scaffold."""

from __future__ import annotations


def has_required_basis_fields(
    currency: str | None,
    unit: str | None,
    share_basis: str | None
) -> bool:
    return all([currency, unit, share_basis])

"""Normalize raw natural-language questions."""

from __future__ import annotations

import re
from typing import Any


def normalize_query(query: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", query).strip()
    entity_hint = None

    match = re.match(r"^\s*([A-Za-z0-9\.\-& ]+?)의\s+", normalized)
    if match:
        entity_hint = match.group(1).strip()
    else:
        token_match = re.search(r"\b[A-Z]{1,6}\b", normalized)
        if token_match:
            entity_hint = token_match.group(0)

    return {
        "raw_query": query,
        "normalized_query": normalized,
        "entity_hint": entity_hint,
    }

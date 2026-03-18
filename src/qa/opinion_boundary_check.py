"""Opinion boundary QA scaffold."""

from __future__ import annotations


def is_boundary_tag_valid(tag: str) -> bool:
    return tag in {"fact", "inference", "opinion", "unknown"}

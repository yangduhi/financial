"""Cross-artifact consistency QA scaffold."""

from __future__ import annotations


def metrics_count_matches(summary_count: int, json_count: int) -> bool:
    return summary_count == json_count

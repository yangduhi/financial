"""Output schema QA scaffold."""

from __future__ import annotations


def has_required_output_files(files_present: set[str]) -> bool:
    required = {"summary.md", "kpi_summary.json", "source_map.json", "review_pack.md"}
    return required.issubset(files_present)

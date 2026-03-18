"""Load MCP practice config files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload if isinstance(payload, dict) else {}


@lru_cache(maxsize=1)
def load_metric_aliases() -> dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "metric_aliases.yaml")


@lru_cache(maxsize=1)
def load_period_rules() -> dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "period_rules.yaml")


@lru_cache(maxsize=1)
def load_doc_type_aliases() -> dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "doc_type_aliases.yaml")


@lru_cache(maxsize=1)
def load_output_paths() -> dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "output_paths.yaml")

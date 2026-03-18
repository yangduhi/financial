"""Runtime helpers for loading local project configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@lru_cache(maxsize=1)
def load_project_env() -> None:
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env", override=False)

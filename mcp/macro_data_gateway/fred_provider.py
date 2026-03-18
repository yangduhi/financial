"""FRED-backed macro data gateway implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from mcp.common.contracts import ToolResponseEnvelope
from mcp.common.errors import ConfigurationError, SourceUnavailableError
from mcp.common.provenance import ProvenanceRecord
from mcp.common.runtime import load_project_env

BASE_URL = "https://api.stlouisfed.org/fred"


def _now() -> datetime:
    return datetime.now(UTC)


def _api_key() -> str:
    import os

    load_project_env()
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ConfigurationError("FRED_API_KEY environment variable is required for FRED.")
    return api_key


def _get_json(path: str, **params: Any) -> Any:
    query = {**params, "api_key": _api_key(), "file_type": "json"}
    url = f"{BASE_URL}/{path}"
    try:
        response = requests.get(url, params=query, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(f"Unable to fetch FRED endpoint '{path}': {exc}") from exc
    return response.json()


def _provenance(source_id: str, as_of_datetime: datetime | None = None) -> list[ProvenanceRecord]:
    observed_at = as_of_datetime or _now()
    return [
        ProvenanceRecord(
            source_id=source_id,
            source_type="macro_data",
            source_system="fred",
            retrieved_at=_now(),
            as_of_datetime=observed_at,
            license_scope="external_public",
            confidence=0.9,
            content_hash=source_id,
        )
    ]


def search_series(search_text: str, limit: int = 10) -> ToolResponseEnvelope:
    payload = _get_json("series/search", search_text=search_text, limit=limit)
    return ToolResponseEnvelope(
        ok=True,
        data={"search_text": search_text, "seriess": payload.get("seriess", [])},
        provenance=_provenance(f"fred-search-{search_text}"),
    )


def get_series_observations(
    series_id: str, limit: int = 12, sort_order: str = "desc"
) -> ToolResponseEnvelope:
    payload = _get_json(
        "series/observations", series_id=series_id, limit=limit, sort_order=sort_order
    )
    observations = payload.get("observations", [])
    as_of_datetime = None
    if observations:
        as_of_datetime = datetime.fromisoformat(f"{observations[0]['date']}T00:00:00+00:00")
    return ToolResponseEnvelope(
        ok=True,
        data={"series_id": series_id, "observations": observations},
        provenance=_provenance(f"fred-series-{series_id}", as_of_datetime),
    )


def get_latest_observation(series_id: str) -> ToolResponseEnvelope:
    response = get_series_observations(series_id=series_id, limit=1, sort_order="desc")
    latest = response.data.get("observations", [])
    return ToolResponseEnvelope(
        ok=bool(latest),
        data={"series_id": series_id, "latest_observation": latest[0] if latest else None},
        provenance=response.provenance,
    )


def get_macro_snapshot(series_ids: list[str]) -> ToolResponseEnvelope:
    snapshot: list[dict[str, Any]] = []
    provenance: list[ProvenanceRecord] = []
    for series_id in series_ids:
        latest = get_latest_observation(series_id)
        snapshot.append(
            {"series_id": series_id, "latest_observation": latest.data["latest_observation"]}
        )
        provenance.extend(latest.provenance)
    return ToolResponseEnvelope(ok=True, data={"snapshot": snapshot}, provenance=provenance)

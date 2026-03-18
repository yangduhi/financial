"""Finnhub-backed market data fallback and verification provider."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from mcp.common.contracts import ToolResponseEnvelope
from mcp.common.errors import ConfigurationError, SourceUnavailableError
from mcp.common.provenance import ProvenanceRecord
from mcp.common.runtime import load_project_env

BASE_URL = "https://finnhub.io/api/v1"


def _now() -> datetime:
    return datetime.now(UTC)


def _token() -> str:
    import os

    load_project_env()
    token = os.getenv("FINNHUB_API_KEY")
    if not token:
        raise ConfigurationError("FINNHUB_API_KEY environment variable is required for Finnhub.")
    return token


def _get_json(path: str, **params: Any) -> Any:
    query = {**params, "token": _token()}
    url = f"{BASE_URL}/{path}"
    try:
        response = requests.get(url, params=query, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(f"Unable to fetch Finnhub endpoint '{path}': {exc}") from exc
    return response.json()


def _provenance(source_id: str, as_of_datetime: datetime | None = None) -> list[ProvenanceRecord]:
    observed_at = as_of_datetime or _now()
    return [
        ProvenanceRecord(
            source_id=source_id,
            source_type="market_data",
            source_system="finnhub",
            retrieved_at=_now(),
            as_of_datetime=observed_at,
            license_scope="external_public",
            confidence=0.8,
            content_hash=source_id,
        )
    ]


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_company_profile(ticker: str) -> ToolResponseEnvelope:
    profile = _get_json("stock/profile2", symbol=ticker)
    return ToolResponseEnvelope(
        ok=bool(profile),
        data={"ticker": ticker, "profile": profile},
        provenance=_provenance(f"{ticker}-profile"),
    )


def get_price_snapshot(ticker: str, as_of_datetime: str | None = None) -> ToolResponseEnvelope:
    target_dt = _parse_dt(as_of_datetime) or _now()
    quote = _get_json("quote", symbol=ticker)
    profile_response = get_company_profile(ticker)
    profile = profile_response.data.get("profile", {})
    return ToolResponseEnvelope(
        ok=bool(quote),
        data={
            "ticker": ticker,
            "snapshot": {
                "close": quote.get("c"),
                "open": quote.get("o"),
                "high": quote.get("h"),
                "low": quote.get("l"),
                "volume": None,
                "as_of_datetime": datetime.fromtimestamp(quote.get("t"), UTC).isoformat()
                if quote.get("t")
                else target_dt.isoformat(),
                "currency": profile.get("currency") or "USD",
                "unit": "price",
                "share_basis": "n/a",
                "vendor": "finnhub",
                "market_session": "regular",
            }
        },
        provenance=_provenance(f"{ticker}-quote", target_dt),
    )


def get_peer_set(
    ticker: str, method: str = "finnhub", max_results: int = 5
) -> ToolResponseEnvelope:
    peers_raw = _get_json("stock/peers", symbol=ticker)
    peers = [{"ticker": symbol} for symbol in peers_raw if symbol != ticker][:max_results]
    return ToolResponseEnvelope(
        ok=True,
        data={"ticker": ticker, "method": method, "peers": peers},
        provenance=_provenance(f"{ticker}-peers"),
    )


def get_basic_financials(ticker: str) -> ToolResponseEnvelope:
    payload = _get_json("stock/metric", symbol=ticker, metric="all")
    return ToolResponseEnvelope(
        ok=bool(payload),
        data={"ticker": ticker, "basic_financials": payload},
        provenance=_provenance(f"{ticker}-metric"),
    )

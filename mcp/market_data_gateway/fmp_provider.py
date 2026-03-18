"""Financial Modeling Prep-backed market data gateway implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from mcp.common.contracts import ToolResponseEnvelope
from mcp.common.errors import ConfigurationError, SourceUnavailableError
from mcp.common.provenance import ProvenanceRecord
from mcp.common.runtime import load_project_env

BASE_URL = "https://financialmodelingprep.com/stable"


def _now() -> datetime:
    return datetime.now(UTC)


def _api_key() -> str:
    import os

    load_project_env()
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        raise ConfigurationError("FMP_API_KEY environment variable is required for FMP requests.")
    return api_key


def _get_json(path: str, **params: Any) -> Any:
    query = {**params, "apikey": _api_key()}
    url = f"{BASE_URL}/{path}"
    try:
        response = requests.get(url, params=query, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(f"Unable to fetch FMP endpoint '{path}': {exc}") from exc
    return response.json()


def _provenance(source_id: str, as_of_datetime: datetime | None = None) -> list[ProvenanceRecord]:
    observed_at = as_of_datetime or _now()
    return [
        ProvenanceRecord(
            source_id=source_id,
            source_type="market_data",
            source_system="financial_modeling_prep_stable",
            retrieved_at=_now(),
            as_of_datetime=observed_at,
            license_scope="external_public",
            confidence=0.85,
            content_hash=source_id,
        )
    ]


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_price_snapshot(ticker: str, as_of_datetime: str | None = None) -> ToolResponseEnvelope:
    target_dt = _parse_dt(as_of_datetime) or _now()
    profile_data = _get_json("profile", symbol=ticker)
    quote = profile_data[0] if isinstance(profile_data, list) and profile_data else {}
    return ToolResponseEnvelope(
        ok=bool(quote),
        data={
            "ticker": ticker,
            "snapshot": {
                "close": quote.get("price"),
                "open": quote.get("open"),
                "high": quote.get("range"),
                "low": quote.get("range"),
                "volume": quote.get("volAvg"),
                "as_of_datetime": target_dt.isoformat(),
                "currency": quote.get("currency") or "USD",
                "unit": "price",
                "share_basis": "n/a",
                "vendor": "financial_modeling_prep_stable",
                "market_session": "regular",
            },
        },
        provenance=_provenance(f"{ticker}-snapshot", target_dt),
    )


def get_price_history(
    ticker: str, start: str, end: str, adjusted: bool = False
) -> ToolResponseEnvelope:
    path = "historical-price-eod/dividend-adjusted" if adjusted else "historical-price-eod/full"
    payload = _get_json(path, symbol=ticker, from_=start, to=end)
    rows = payload if isinstance(payload, list) else payload.get("historical", [])
    return ToolResponseEnvelope(
        ok=True,
        data={"ticker": ticker, "rows": rows},
        provenance=_provenance(f"{ticker}-history"),
    )


def get_fundamentals(
    ticker: str, period: str = "quarterly", as_of_datetime: str | None = None
) -> ToolResponseEnvelope:
    target_dt = _parse_dt(as_of_datetime) or _now()
    profile = _get_json("profile", symbol=ticker)
    income = _get_json("income-statement", symbol=ticker, period=period, limit=4)
    balance = _get_json("balance-sheet-statement", symbol=ticker, period=period, limit=4)
    cashflow = _get_json("cash-flow-statement", symbol=ticker, period=period, limit=4)
    enterprise = _get_json("enterprise-values", symbol=ticker, period=period, limit=4)
    profile_row = profile[0] if isinstance(profile, list) and profile else {}
    return ToolResponseEnvelope(
        ok=True,
        data={
            "ticker": ticker,
            "period": period,
            "currency": profile_row.get("currency"),
            "profile": profile_row,
            "income_statement": income,
            "balance_sheet": balance,
            "cashflow": cashflow,
            "enterprise_values": enterprise,
        },
        provenance=_provenance(f"{ticker}-fundamentals", target_dt),
    )


def get_share_count(
    ticker: str, basis: str = "diluted", as_of_datetime: str | None = None
) -> ToolResponseEnvelope:
    target_dt = _parse_dt(as_of_datetime) or _now()
    payload = _get_json("shares-float", symbol=ticker)
    row = payload[0] if isinstance(payload, list) and payload else {}
    return ToolResponseEnvelope(
        ok=bool(row),
        data={
            "ticker": ticker,
            "share_basis": basis,
            "shares_outstanding": row.get("outstandingShares"),
            "float_shares": row.get("floatShares"),
            "free_float": row.get("freeFloat"),
            "vendor": "financial_modeling_prep_stable",
            "as_of_datetime": target_dt.isoformat(),
        },
        provenance=_provenance(f"{ticker}-shares", target_dt),
    )


def get_fx_rate(base: str, quote: str, as_of_datetime: str | None = None) -> ToolResponseEnvelope:
    target_dt = _parse_dt(as_of_datetime) or _now()
    if base == quote:
        return ToolResponseEnvelope(
            ok=True,
            data={
                "base": base,
                "quote": quote,
                "rate": 1.0,
                "as_of_datetime": target_dt.isoformat(),
            },
            provenance=_provenance(f"{base}{quote}-fx", target_dt),
        )

    symbol = f"{base}{quote}"
    snapshot = get_price_snapshot(symbol, as_of_datetime=as_of_datetime)
    snapshot_data = snapshot.data.get("snapshot") or {}
    return ToolResponseEnvelope(
        ok=snapshot.ok,
        data={
            "base": base,
            "quote": quote,
            "rate": snapshot_data.get("close"),
            "as_of_datetime": snapshot_data.get("as_of_datetime") or target_dt.isoformat(),
        },
        provenance=_provenance(f"{symbol}-fx", target_dt),
    )


def get_peer_set(ticker: str, method: str = "fmp", max_results: int = 5) -> ToolResponseEnvelope:
    payload = _get_json("stock-peers", symbol=ticker)
    peers: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            symbol = item.get("symbol")
            if not symbol or symbol == ticker:
                continue
            peers.append(
                {
                    "ticker": symbol,
                    "company_name": item.get("companyName"),
                    "price": item.get("price"),
                    "market_cap": item.get("mktCap"),
                }
            )
            if len(peers) >= max_results:
                break
    return ToolResponseEnvelope(
        ok=True,
        data={"ticker": ticker, "method": method, "peers": peers},
        provenance=_provenance(f"{ticker}-peers"),
    )

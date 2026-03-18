"""yfinance-backed market data gateway implementation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import yfinance as yf

from mcp.common.contracts import ToolResponseEnvelope
from mcp.common.provenance import ProvenanceRecord


def _now() -> datetime:
    return datetime.now(UTC)


def _provenance(source_id: str) -> list[ProvenanceRecord]:
    return [
        ProvenanceRecord(
            source_id=source_id,
            source_type="market_data",
            source_system="yahoo_finance_yfinance",
            retrieved_at=_now(),
            as_of_datetime=_now(),
            license_scope="external_public",
            confidence=0.7,
            content_hash=source_id,
        )
    ]


def _ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol)


def _to_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_price_snapshot(ticker: str, as_of_datetime: str | None = None) -> ToolResponseEnvelope:
    target = _to_datetime(as_of_datetime) or _now()
    start = (target - timedelta(days=7)).date().isoformat()
    end = (target + timedelta(days=1)).date().isoformat()
    history = _ticker(ticker).history(start=start, end=end, auto_adjust=False)
    history = history.dropna(subset=["Close"])
    if history.empty:
        return ToolResponseEnvelope(
            ok=False,
            errors=[],
            data={"ticker": ticker, "snapshot": None},
            provenance=_provenance(f"{ticker}-snapshot"),
        )

    row = history.iloc[-1]
    timestamp = history.index[-1].to_pydatetime()
    return ToolResponseEnvelope(
        ok=True,
        data={
            "ticker": ticker,
            "snapshot": {
                "close": float(row["Close"]),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "volume": float(row["Volume"]),
                "as_of_datetime": timestamp.isoformat(),
                "currency": "USD",
                "unit": "price",
                "share_basis": "n/a",
                "vendor": "yahoo_finance_yfinance",
                "market_session": "regular",
            },
        },
        provenance=_provenance(f"{ticker}-snapshot"),
    )


def get_price_history(
    ticker: str, start: str, end: str, adjusted: bool = False
) -> ToolResponseEnvelope:
    history = _ticker(ticker).history(start=start, end=end, auto_adjust=adjusted)
    rows = []
    for index, row in history.iterrows():
        rows.append(
            {
                "date": index.to_pydatetime().date().isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        )
    return ToolResponseEnvelope(
        ok=True, data={"ticker": ticker, "rows": rows}, provenance=_provenance(f"{ticker}-history")
    )


def get_fundamentals(
    ticker: str, period: str = "quarterly", as_of_datetime: str | None = None
) -> ToolResponseEnvelope:
    del as_of_datetime
    ticker_obj = _ticker(ticker)
    income_stmt = (
        ticker_obj.quarterly_income_stmt if period == "quarterly" else ticker_obj.income_stmt
    )
    balance_sheet = (
        ticker_obj.quarterly_balance_sheet if period == "quarterly" else ticker_obj.balance_sheet
    )
    cashflow = ticker_obj.quarterly_cashflow if period == "quarterly" else ticker_obj.cashflow
    info = ticker_obj.info or {}

    def frame_to_records(frame) -> list[dict[str, Any]]:
        if frame is None or frame.empty:
            return []
        records: list[dict[str, Any]] = []
        for column in frame.columns:
            values: dict[str, Any] = {}
            for index in frame.index[:20]:
                raw_value = frame.at[index, column]
                if raw_value is None:
                    continue
                try:
                    values[str(index)] = float(raw_value)
                except (TypeError, ValueError):
                    values[str(index)] = str(raw_value)
            records.append(
                {
                    "period_end": str(column.date() if hasattr(column, "date") else column),
                    "values": values,
                }
            )
        return records

    return ToolResponseEnvelope(
        ok=True,
        data={
            "ticker": ticker,
            "period": period,
            "currency": info.get("financialCurrency") or info.get("currency"),
            "market_cap": info.get("marketCap"),
            "income_statement": frame_to_records(income_stmt),
            "balance_sheet": frame_to_records(balance_sheet),
            "cashflow": frame_to_records(cashflow),
        },
        provenance=_provenance(f"{ticker}-fundamentals"),
    )


def get_share_count(
    ticker: str, basis: str = "diluted", as_of_datetime: str | None = None
) -> ToolResponseEnvelope:
    del as_of_datetime
    info = _ticker(ticker).info or {}
    return ToolResponseEnvelope(
        ok=True,
        data={
            "ticker": ticker,
            "share_basis": basis,
            "shares_outstanding": info.get("sharesOutstanding"),
            "implied_shares_outstanding": info.get("impliedSharesOutstanding"),
            "currency": info.get("currency"),
            "vendor": "yahoo_finance_yfinance",
        },
        provenance=_provenance(f"{ticker}-shares"),
    )


def get_fx_rate(base: str, quote: str, as_of_datetime: str | None = None) -> ToolResponseEnvelope:
    if base == quote:
        rate = 1.0
        observed_at = (_to_datetime(as_of_datetime) or _now()).isoformat()
        return ToolResponseEnvelope(
            ok=True,
            data={"base": base, "quote": quote, "rate": rate, "as_of_datetime": observed_at},
            provenance=_provenance(f"{base}{quote}-fx"),
        )

    pair = f"{base}{quote}=X"
    snapshot = get_price_snapshot(pair, as_of_datetime=as_of_datetime)
    price = snapshot.data.get("snapshot", {}).get("close") if snapshot.ok else None
    return ToolResponseEnvelope(
        ok=price is not None,
        data={"base": base, "quote": quote, "rate": price, "as_of_datetime": as_of_datetime},
        provenance=_provenance(f"{pair}-fx"),
    )


def get_peer_set(ticker: str, method: str = "search", max_results: int = 5) -> ToolResponseEnvelope:
    info = _ticker(ticker).info or {}
    industry_query = info.get("industry") or info.get("sector") or ticker
    peers: list[dict[str, Any]] = []
    if hasattr(yf, "Search"):
        try:
            search = yf.Search(query=industry_query, max_results=max_results + 1)
            for quote in getattr(search, "quotes", []) or []:
                symbol = quote.get("symbol")
                if not symbol or symbol == ticker:
                    continue
                peers.append(
                    {
                        "ticker": symbol,
                        "shortname": quote.get("shortname") or quote.get("longname"),
                        "exchange": quote.get("exchange"),
                    }
                )
                if len(peers) >= max_results:
                    break
        except Exception:
            peers = []

    return ToolResponseEnvelope(
        ok=True,
        data={"ticker": ticker, "method": method, "query": industry_query, "peers": peers},
        provenance=_provenance(f"{ticker}-peers"),
    )

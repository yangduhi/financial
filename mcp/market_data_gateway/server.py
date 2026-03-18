"""Market data MCP gateway backed by FMP with yfinance fallback."""

from __future__ import annotations

from dataclasses import dataclass

from mcp.common.errors import ConfigurationError, SourceUnavailableError

from . import finnhub_provider, fmp_provider, yfinance_provider


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str


MARKET_DATA_GATEWAY_TOOLS = [
    ToolDefinition("get_price_snapshot", "Return a point-in-time price snapshot."),
    ToolDefinition("get_price_history", "Return historical price data."),
    ToolDefinition("get_fundamentals", "Return structured fundamentals."),
    ToolDefinition("get_share_count", "Return point-in-time share counts."),
    ToolDefinition("get_fx_rate", "Return point-in-time FX rates."),
    ToolDefinition("get_peer_set", "Return peer candidates for an issuer."),
]


def list_tools() -> list[ToolDefinition]:
    """Return the supported tools for the scaffold server."""

    return MARKET_DATA_GATEWAY_TOOLS


def _try_chain(*callables, **kwargs):
    last_response = None
    for callable_ in callables:
        try:
            response = callable_(**kwargs)
            last_response = response
            if getattr(response, "ok", False):
                return response
        except (ConfigurationError, SourceUnavailableError):
            continue
    return last_response


def _attach_quote_verification(response, ticker: str, as_of_datetime: str | None = None):
    try:
        verification = finnhub_provider.get_price_snapshot(
            ticker=ticker, as_of_datetime=as_of_datetime
        )
    except (ConfigurationError, SourceUnavailableError):
        return response

    snapshot = response.data.get("snapshot") or {}
    verification_snapshot = verification.data.get("snapshot") or {}
    close_value = snapshot.get("close")
    verification_close = verification_snapshot.get("close")
    response.data["verification"] = {
        "provider": "finnhub",
        "close": verification_close,
        "as_of_datetime": verification_snapshot.get("as_of_datetime"),
        "delta": (
            None
            if close_value is None or verification_close is None
            else abs(float(close_value) - float(verification_close))
        ),
    }
    return response


def _attach_peer_verification(response, ticker: str):
    try:
        verification = finnhub_provider.get_peer_set(ticker=ticker)
    except (ConfigurationError, SourceUnavailableError):
        return response

    response.data["verification"] = {
        "provider": "finnhub",
        "peers": verification.data.get("peers", []),
    }
    return response


def _attach_profile_verification(response, ticker: str):
    try:
        profile = finnhub_provider.get_company_profile(ticker=ticker)
        metrics = finnhub_provider.get_basic_financials(ticker=ticker)
    except (ConfigurationError, SourceUnavailableError):
        return response

    response.data["verification"] = {
        "provider": "finnhub",
        "profile": profile.data.get("profile", {}),
        "basic_financials": metrics.data.get("basic_financials", {}),
    }
    return response


def get_price_snapshot(**kwargs):
    response = _try_chain(
        fmp_provider.get_price_snapshot,
        finnhub_provider.get_price_snapshot,
        yfinance_provider.get_price_snapshot,
        **kwargs
    )
    if response is None:
        raise SourceUnavailableError("No market data provider produced a price snapshot.")
    return _attach_quote_verification(
        response, ticker=kwargs["ticker"], as_of_datetime=kwargs.get("as_of_datetime")
    )


def get_price_history(**kwargs):
    response = _try_chain(
        fmp_provider.get_price_history, yfinance_provider.get_price_history, **kwargs
    )
    if response is None:
        raise SourceUnavailableError("No market data provider produced price history.")
    return response


def get_fundamentals(**kwargs):
    response = _try_chain(
        fmp_provider.get_fundamentals, yfinance_provider.get_fundamentals, **kwargs
    )
    if response is None:
        raise SourceUnavailableError("No market data provider produced fundamentals.")
    return _attach_profile_verification(response, ticker=kwargs["ticker"])


def get_share_count(**kwargs):
    response = _try_chain(fmp_provider.get_share_count, yfinance_provider.get_share_count, **kwargs)
    if response is None:
        raise SourceUnavailableError("No market data provider produced share counts.")
    return response


def get_fx_rate(**kwargs):
    response = _try_chain(fmp_provider.get_fx_rate, yfinance_provider.get_fx_rate, **kwargs)
    if response is None:
        raise SourceUnavailableError("No market data provider produced FX rates.")
    return response


def get_peer_set(**kwargs):
    response = _try_chain(
        fmp_provider.get_peer_set,
        finnhub_provider.get_peer_set,
        yfinance_provider.get_peer_set,
        **kwargs
    )
    if response is None:
        raise SourceUnavailableError("No market data provider produced peer candidates.")
    return _attach_peer_verification(response, ticker=kwargs["ticker"])

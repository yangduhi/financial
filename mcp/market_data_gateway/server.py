"""Market data MCP gateway backed by FMP with yfinance fallback."""

from __future__ import annotations

from dataclasses import dataclass

from mcp.common.errors import ConfigurationError, SourceUnavailableError

from . import fmp_provider, yfinance_provider


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


def _with_fallback(primary_callable, fallback_callable, **kwargs):
    try:
        response = primary_callable(**kwargs)
        if getattr(response, "ok", False):
            return response
    except (ConfigurationError, SourceUnavailableError):
        pass
    return fallback_callable(**kwargs)


def get_price_snapshot(**kwargs):
    return _with_fallback(
        fmp_provider.get_price_snapshot, yfinance_provider.get_price_snapshot, **kwargs
    )


def get_price_history(**kwargs):
    return _with_fallback(
        fmp_provider.get_price_history, yfinance_provider.get_price_history, **kwargs
    )


def get_fundamentals(**kwargs):
    return _with_fallback(
        fmp_provider.get_fundamentals, yfinance_provider.get_fundamentals, **kwargs
    )


def get_share_count(**kwargs):
    return _with_fallback(
        fmp_provider.get_share_count, yfinance_provider.get_share_count, **kwargs
    )


def get_fx_rate(**kwargs):
    return _with_fallback(fmp_provider.get_fx_rate, yfinance_provider.get_fx_rate, **kwargs)


def get_peer_set(**kwargs):
    return _with_fallback(fmp_provider.get_peer_set, yfinance_provider.get_peer_set, **kwargs)

"""Scaffold for the market data MCP gateway."""

from __future__ import annotations

from dataclasses import dataclass


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
    ToolDefinition("get_peer_set", "Return peer candidates for an issuer.")
]


def list_tools() -> list[ToolDefinition]:
    """Return the supported tools for the scaffold server."""

    return MARKET_DATA_GATEWAY_TOOLS

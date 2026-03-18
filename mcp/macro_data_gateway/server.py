"""Macro data gateway backed by FRED."""

from __future__ import annotations

from dataclasses import dataclass

from . import fred_provider


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str


MACRO_GATEWAY_TOOLS = [
    ToolDefinition("search_series", "Search FRED series metadata."),
    ToolDefinition("get_series_observations", "Fetch FRED observations for a series."),
    ToolDefinition("get_latest_observation", "Fetch the latest FRED observation for a series."),
    ToolDefinition("get_macro_snapshot", "Fetch a latest-value macro snapshot across series."),
]


def list_tools() -> list[ToolDefinition]:
    return MACRO_GATEWAY_TOOLS


def search_series(**kwargs):
    return fred_provider.search_series(**kwargs)


def get_series_observations(**kwargs):
    return fred_provider.get_series_observations(**kwargs)


def get_latest_observation(**kwargs):
    return fred_provider.get_latest_observation(**kwargs)


def get_macro_snapshot(**kwargs):
    return fred_provider.get_macro_snapshot(**kwargs)

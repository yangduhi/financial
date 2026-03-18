"""Helpers for quarterly metric extraction and trend computation."""

from __future__ import annotations

from datetime import datetime
from statistics import pstdev
from typing import Any

from .config_loader import load_metric_aliases


def period_label_from_period_end(period_end: str) -> str:
    dt = datetime.fromisoformat(period_end).date()
    quarter = ((dt.month - 1) // 3) + 1
    return f"{dt.year}Q{quarter}"


def metric_provider_keys(metric: str) -> dict[str, list[str]]:
    aliases = load_metric_aliases().get("metrics", {})
    return aliases.get(metric, {}).get("provider_keys", {})


def extract_metric_series(fundamentals: dict[str, Any], metric: str) -> list[dict[str, Any]]:
    provider_keys = metric_provider_keys(metric)
    series: list[dict[str, Any]] = []
    for section_name, candidate_keys in provider_keys.items():
        rows = fundamentals.get(section_name, []) or []
        for row in rows:
            values = row.get("values", row)
            period_end = row.get("period_end") or row.get("date")
            if not period_end:
                continue
            value = None
            for candidate in candidate_keys:
                if candidate in values and values[candidate] is not None:
                    value = values[candidate]
                    break
            series.append({"period_end": period_end, "value": value, "section": section_name})
        if series:
            break

    series.sort(key=lambda item: item["period_end"])
    return series


def build_trend_series(series: list[dict[str, Any]], quarter_count: int) -> list[dict[str, Any]]:
    trimmed = series[-max(quarter_count, 8) :]
    output: list[dict[str, Any]] = []
    for index, item in enumerate(trimmed):
        value = item["value"]
        qoq = None
        yoy = None
        if index > 0:
            prev = trimmed[index - 1]["value"]
            if value is not None and prev not in (None, 0):
                qoq = ((float(value) - float(prev)) / abs(float(prev))) * 100.0
        if index >= 4:
            prev_year = trimmed[index - 4]["value"]
            if value is not None and prev_year not in (None, 0):
                yoy = ((float(value) - float(prev_year)) / abs(float(prev_year))) * 100.0
        output.append(
            {
                "period_label": period_label_from_period_end(item["period_end"]),
                "period_end": item["period_end"],
                "value": value,
                "qoq_change_pct": qoq,
                "yoy_change_pct": yoy,
            }
        )
    return output[-quarter_count:]


def build_summary_flags(series: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(item["value"]) for item in series if item["value"] is not None]
    qoq_values = [item["qoq_change_pct"] for item in series if item["qoq_change_pct"] is not None]
    if len(values) < 2:
        return {
            "overall_direction": "FLAT",
            "volatility": "UNKNOWN",
            "largest_move_period": None,
            "latest_qoq_direction": "UNKNOWN",
        }

    if values[-1] > values[0]:
        overall_direction = "UP"
    elif values[-1] < values[0]:
        overall_direction = "DOWN"
    else:
        overall_direction = "FLAT"
    if not qoq_values:
        volatility = "UNKNOWN"
    else:
        std = pstdev(qoq_values)
        volatility = "LOW" if std < 5 else "MEDIUM" if std < 15 else "HIGH"

    largest_move_period = None
    if qoq_values:
        largest = max(
            (item for item in series if item["qoq_change_pct"] is not None),
            key=lambda row: abs(float(row["qoq_change_pct"])),
        )
        largest_move_period = largest["period_label"]

    latest_qoq = series[-1].get("qoq_change_pct")
    if latest_qoq and latest_qoq > 0:
        latest_qoq_direction = "UP"
    elif latest_qoq and latest_qoq < 0:
        latest_qoq_direction = "DOWN"
    else:
        latest_qoq_direction = "FLAT"

    return {
        "overall_direction": overall_direction,
        "volatility": volatility,
        "largest_move_period": largest_move_period,
        "latest_qoq_direction": latest_qoq_direction,
    }

"""Parse normalized Korean finance questions into canonical intent."""

from __future__ import annotations

import re
from typing import Any

from .config_loader import load_metric_aliases, load_period_rules

EVIDENCE_KEYWORDS = ["문장", "언급", "가이던스", "실적 발표", "10-Q", "10-K", "보여줘"]
COMPARE_KEYWORDS = ["전분기", "직전 분기", "비교", "얼마나 늘", "얼마나 줄"]
TREND_KEYWORDS = ["최근 4분기", "추세", "변동", "흐름"]
AMBIGUOUS_METRICS = {"마진", "이익", "실적"}


def _extract_metric(query: str) -> dict[str, Any]:
    aliases = load_metric_aliases().get("metrics", {})
    lowered = query.lower()
    for canonical, config in aliases.items():
        for alias in config.get("aliases_ko", []) + config.get("aliases_en", []):
            if alias.lower() in lowered:
                return {
                    "status": "OK",
                    "metric": canonical,
                    "label_ko": config.get("label_ko", canonical),
                    "matched_alias": alias,
                }
    for ambiguous in AMBIGUOUS_METRICS:
        if ambiguous in query:
            return {"status": "AMBIGUOUS_METRIC", "metric": None, "matched_alias": ambiguous}
    return {"status": "NOT_FOUND", "metric": None, "matched_alias": None}


def _extract_period(query: str) -> dict[str, Any]:
    period_rules = load_period_rules()
    for rule in period_rules.get("patterns", {}).get("recent_quarters", []):
        match = re.search(rule["regex"], query)
        if not match:
            continue
        if "fixed_value" in rule:
            return {"type": rule["type"], "value": rule["fixed_value"]}
        return {"type": rule["type"], "value": int(match.group(1))}

    for rule in period_rules.get("patterns", {}).get("evidence_recent", []):
        if re.search(rule["regex"], query):
            return {"type": rule["type"], "value": 1}

    default_value = period_rules.get("defaults", {}).get("recent_trend_quarters", 4)
    return {"type": "recent_quarters", "value": default_value}


def _extract_comparison(query: str) -> str:
    period_rules = load_period_rules()
    for rule in period_rules.get("patterns", {}).get("qoq_compare", []):
        if re.search(rule["regex"], query):
            return rule["comparison"]
    return "sequential_trend"


def parse_intent(query: str, entity_hint: str | None = None) -> dict[str, Any]:
    metric_info = _extract_metric(query)
    period_info = _extract_period(query)
    comparison = _extract_comparison(query)

    lowered = query.lower()
    if metric_info["status"] == "AMBIGUOUS_METRIC":
        return {
            "status": "AMBIGUOUS_METRIC",
            "entity_hint": entity_hint,
            "metric": None,
            "period": period_info,
            "comparison": comparison,
            "intent": None,
        }

    if any(keyword in query for keyword in EVIDENCE_KEYWORDS):
        intent = "filing_evidence"
    elif any(keyword in query for keyword in COMPARE_KEYWORDS):
        intent = "metric_compare"
    elif any(keyword in query for keyword in TREND_KEYWORDS) or metric_info["metric"]:
        intent = "metric_trend"
    else:
        intent = None

    if not intent:
        return {
            "status": "UNSUPPORTED_INTENT",
            "entity_hint": entity_hint,
            "metric": metric_info["metric"],
            "period": period_info,
            "comparison": comparison,
            "intent": None,
        }

    topic = None
    if "가이던스" in query or "guidance" in lowered:
        topic = "guidance"

    return {
        "status": "OK",
        "entity_hint": entity_hint,
        "intent": intent,
        "metric": metric_info["metric"],
        "metric_label_ko": metric_info.get("label_ko"),
        "period": period_info,
        "comparison": comparison,
        "response_mode": "summary_with_evidence",
        "topic": topic,
        "matched_alias": metric_info["matched_alias"],
    }

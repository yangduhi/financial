"""Generate grounded Korean answers from intent-tool outputs."""

from __future__ import annotations

from typing import Any

from .config_loader import load_metric_aliases


def generate_metric_trend_answer(
    entity_name: str,
    metric: str,
    trend_result: dict[str, Any],
    evidence_result: dict[str, Any] | None = None,
) -> str:
    metric_aliases = load_metric_aliases().get("metrics", {})
    metric_label = metric_aliases.get(metric, {}).get("label_ko", metric)
    series = trend_result.get("series", [])
    if not series:
        return f"{entity_name}의 {metric_label} 추세를 확인할 수 있는 데이터가 없습니다."

    latest = series[-1]
    direction = trend_result.get("trend_flags", {}).get("overall_direction", "FLAT")
    direction_ko = {"UP": "증가", "DOWN": "감소", "FLAT": "유지"}.get(direction, "유지")

    lines = [
        (
            f"{entity_name}의 최근 {len(series)}분기 {metric_label}은 "
            f"전반적으로 {direction_ko} 흐름이었습니다."
        ),
        "",
        "핵심 수치:",
    ]
    for row in series:
        qoq = row.get("qoq_change_pct")
        qoq_text = "n/a" if qoq is None else f"{qoq:.1f}%"
        lines.append(f"- {row['period_label']}: {row['value']} (q/q: {qoq_text})")

    lines.extend(
        [
            "",
            "해석:",
            f"- 최신 분기 값은 {latest['period_label']} 기준 {latest['value']}입니다.",
        ]
    )

    evidence = (evidence_result or {}).get("evidence", []) if evidence_result else []
    if evidence:
        lines.extend(
            [
                "",
                "근거:",
                f"- {evidence[0]['citation_text']}",
                "",
                "제한:",
                "- 일부 값은 provider fallback 결과일 수 있습니다.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "근거:",
                "- metric source metadata는 확보되었으나 추가 excerpt는 생략했습니다.",
            ]
        )

    return "\n".join(lines)


def _metric_label(metric: str) -> str:
    metric_aliases = load_metric_aliases().get("metrics", {})
    return metric_aliases.get(metric, {}).get("label_ko", metric)


def _topic_label(topic: str | None) -> str:
    mapping = {
        "guidance": "가이던스",
        "outlook": "아웃룩",
        None: "관련",
    }
    return mapping.get(topic, topic or "관련")


def _format_value(value: Any, metric: str) -> str:
    if value is None:
        return "[UNKNOWN]"
    if metric == "eps":
        return f"{float(value):.2f}"
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def generate_metric_compare_answer(
    entity_name: str,
    metrics_result: dict[str, Any],
    metric: str | None = None,
    evidence_result: dict[str, Any] | None = None,
) -> str:
    periods = metrics_result.get("periods", [])
    if len(periods) < 2:
        return f"{entity_name}의 최근 분기와 직전 분기를 비교할 수 있는 데이터가 부족합니다."

    previous = periods[-2]
    latest = periods[-1]
    evidence = (evidence_result or {}).get("evidence", []) if evidence_result else []

    if metric:
        label = _metric_label(metric)
        prev_value = previous["values"].get(metric)
        latest_value = latest["values"].get(metric)
        if prev_value in (None, 0) or latest_value is None:
            return f"{entity_name}의 {label}은 비교 가능한 값이 부족합니다."

        delta = float(latest_value) - float(prev_value)
        delta_pct = (delta / abs(float(prev_value))) * 100.0
        direction = "증가" if delta > 0 else "감소" if delta < 0 else "유지"

        lines = [
            f"{entity_name}의 {label}은 최근 분기 기준 직전 분기 대비 {direction}했습니다.",
            "",
            "핵심 수치:",
            f"- 직전 분기 {previous['period_label']}: {_format_value(prev_value, metric)}",
            f"- 최근 분기 {latest['period_label']}: {_format_value(latest_value, metric)}",
            f"- 증감률: {delta_pct:.1f}%",
            "",
            "해석:",
            (
                f"- {latest['period_label']} 기준 {label}은 "
                f"{previous['period_label']} 대비 {direction} 방향입니다."
            ),
        ]
    else:
        improvements: list[str] = []
        for candidate_metric, latest_value in latest["values"].items():
            previous_value = previous["values"].get(candidate_metric)
            if previous_value in (None, 0) or latest_value is None:
                continue
                delta = float(latest_value) - float(previous_value)
                if delta > 0:
                    delta_pct = (delta / abs(float(previous_value))) * 100.0
                    improvements.append(
                        f"- {_metric_label(candidate_metric)}: "
                        f"{previous['period_label']} -> {latest['period_label']} "
                        f"({delta_pct:.1f}%)"
                    )

        lines = [
            f"{entity_name}의 최근 분기에서 직전 분기 대비 개선된 항목은 아래와 같습니다.",
            "",
            "핵심 수치:",
        ]
        if improvements:
            lines.extend(improvements)
        else:
            lines.append("- 개선된 핵심 항목을 확정할 데이터가 부족합니다.")

        lines.extend(
            [
                "",
                "해석:",
                f"- 비교 기준은 {previous['period_label']} 대비 {latest['period_label']}입니다.",
            ]
        )

    if evidence:
        lines.extend(["", "근거:", f"- {evidence[0]['citation_text']}"])
    else:
        lines.extend(["", "근거:", "- 추가 근거 excerpt는 확보되지 않았습니다."])
    return "\n".join(lines)


def generate_filing_evidence_answer(
    entity_name: str,
    topic: str | None,
    filings_result: dict[str, Any],
    evidence_result: dict[str, Any],
) -> str:
    evidence = evidence_result.get("evidence", [])
    filings = filings_result.get("items", [])
    topic_label = _topic_label(topic)

    if evidence:
        lines = [
            f"{entity_name}의 최근 문서에서 {topic_label} 관련 핵심 문장은 아래와 같습니다.",
            "",
            "근거 문장:",
        ]
        for item in evidence[:3]:
            lines.append(f"- {item['excerpt']}")
            lines.append(f"  출처: {item['citation_text']}")
        return "\n".join(lines)

    lines = [
        (
            f"{entity_name}의 최근 문서에서 {topic_label} 관련 "
            f"직접 근거 문장을 충분히 확보하지 못했습니다."
        )
    ]
    if filings:
        filing_lines = [f"- {item['filing_date']} {item['doc_type']}" for item in filings[:3]]
        lines.extend(
            [
                "",
                "확인한 최근 문서:",
                *filing_lines,
            ]
        )
    lines.extend(
        ["", "제한:", "- 현재 확보된 최근 문서 기준에서 direct excerpt 매칭이 부족했습니다."]
    )
    return "\n".join(lines)

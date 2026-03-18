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

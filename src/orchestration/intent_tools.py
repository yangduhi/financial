"""Intent-level tools for natural-language MCP practice."""

from __future__ import annotations

from typing import Any, cast

from mcp.docs_gateway import server as docs_server
from mcp.docs_gateway.sec_edgar import load_company_tickers
from mcp.market_data_gateway import server as market_server

from .config_loader import load_doc_type_aliases, load_metric_aliases
from .trend_service import build_summary_flags, build_trend_series, extract_metric_series


def _canonical_identifier(ticker: str, market_hint: str = "us") -> str:
    return f"{ticker.lower()}_{market_hint.lower()}_equity"


def _ticker_from_identifier(identifier: str) -> str:
    return identifier.split("_", 1)[0].upper()


def resolve_entity(
    query: str,
    entity_type: str = "public_company",
    market_hint: str = "US",
    max_candidates: int = 5,
) -> dict[str, Any]:
    del entity_type
    lowered = query.strip().lower()
    records = load_company_tickers()
    exact = [row for row in records if row["ticker"].lower() == lowered]
    partial = [
        row
        for row in records
        if lowered in row["title"].lower() or row["ticker"].lower().startswith(lowered)
    ]
    candidates_raw = exact if exact else partial

    candidates = [
        {
            "identifier": _canonical_identifier(row["ticker"], market_hint),
            "ticker": row["ticker"],
            "exchange": "US",
            "company_name": row["title"],
        }
        for row in candidates_raw[:max_candidates]
    ]

    if len(candidates) == 1:
        return {
            "status": "RESOLVED",
            "selected": candidates[0],
            "candidates": [],
            "confidence": 0.99 if exact else 0.8,
            "source": "sec_company_tickers",
            "resolution_method": "ticker_exact" if exact else "name_partial",
            "matched_alias": query,
        }
    if len(candidates) > 1:
        return {
            "status": "AMBIGUOUS",
            "selected": None,
            "candidates": candidates,
            "confidence": 0.0,
            "source": "sec_company_tickers",
            "resolution_method": "multiple_candidates",
            "matched_alias": query,
        }
    return {
        "status": "NOT_FOUND",
        "selected": None,
        "candidates": [],
        "confidence": 0.0,
        "source": "sec_company_tickers",
        "resolution_method": "none",
        "matched_alias": query,
    }


def get_recent_filings(
    identifier: str, doc_types: list[str], limit: int = 5, sort: str = "filing_date_desc"
) -> dict[str, Any]:
    del sort
    ticker = _ticker_from_identifier(identifier)
    alias_map = load_doc_type_aliases().get("logical_to_source", {})
    mapped_doc_types: list[str] = []
    for doc_type in doc_types:
        mapped_doc_types.extend(alias_map.get(doc_type, [doc_type]))
    response = docs_server.search_documents(query=None, company=ticker, doc_types=mapped_doc_types)
    items = []
    for row in response.data.get("results", [])[:limit]:
        items.append(
            {
                "doc_id": row["document_id"],
                "doc_type": row["document_type"],
                "title": row["title"],
                "filing_date": row["published_at"],
                "period_label": None,
                "uri": row["uri"],
            }
        )
    return {"status": "OK" if items else "NOT_FOUND", "items": items}


def _best_effort_sources(identifier: str, limit: int) -> list[dict[str, Any]]:
    filings = get_recent_filings(identifier, ["10-Q", "10-K"], limit=limit)
    return filings.get("items", [])


def get_quarterly_metrics(
    identifier: str,
    metrics: list[str],
    quarter_count: int = 4,
    period_basis: str = "fiscal_reported",
    include_source: bool = True,
) -> dict[str, Any]:
    del period_basis
    ticker = _ticker_from_identifier(identifier)
    fundamentals = market_server.get_fundamentals(ticker=ticker, period="quarter").data
    sources = _best_effort_sources(identifier, limit=max(quarter_count, len(metrics)))
    unit_map: dict[str, str] = {}
    by_metric = {metric: extract_metric_series(fundamentals, metric) for metric in metrics}

    base_series = next((series for series in by_metric.values() if series), [])
    base_periods = base_series[-quarter_count:]
    periods: list[dict[str, Any]] = []

    for index, period in enumerate(base_periods):
        fiscal_quarter = ((int(period["period_end"][5:7]) - 1) // 3) + 1
        period_label = period["period_end"][:4] + "Q" + str(fiscal_quarter)
        values: dict[str, Any] = {}
        for metric in metrics:
            series = by_metric.get(metric, [])
            match = next(
                (item for item in series if item["period_end"] == period["period_end"]),
                None,
            )
            values[metric] = match["value"] if match else None
            unit_map[metric] = "USD_per_share" if metric == "eps" else "USD"

        source_info = sources[index] if include_source and index < len(sources) else None
        periods.append(
            {
                "period_label": period_label,
                "fiscal_year": int(period["period_end"][:4]),
                "fiscal_quarter": int(fiscal_quarter),
                "values": values,
                "source": source_info,
                "data_quality_flag": (
                    "best_effort_source_mapping" if source_info else "missing_source"
                ),
            }
        )

    status = "OK" if periods else "NOT_FOUND"
    if periods and any(any(value is None for value in item["values"].values()) for item in periods):
        status = "PARTIAL"

    return {
        "status": status,
        "identifier": identifier,
        "currency": fundamentals.get("currency") or "USD",
        "unit_map": unit_map,
        "periods": periods,
    }


def get_metric_trend(
    identifier: str,
    metric: str,
    quarter_count: int = 4,
    include_qoq: bool = True,
    include_yoy: bool = True,
    include_summary_flags: bool = True,
) -> dict[str, Any]:
    request_quarters = max(quarter_count, 8 if include_yoy else quarter_count)
    metric_payload = get_quarterly_metrics(identifier, [metric], quarter_count=request_quarters)
    periods = metric_payload.get("periods", [])
    raw_series = [
        {
            "period_label": item["period_label"],
            "period_end": f"{item['fiscal_year']}-{item['fiscal_quarter'] * 3:02d}-01",
            "value": item["values"].get(metric),
        }
        for item in periods
    ]

    series = build_trend_series(raw_series, quarter_count=quarter_count)
    if not include_qoq:
        for row in series:
            row["qoq_change_pct"] = None
    if not include_yoy:
        for row in series:
            row["yoy_change_pct"] = None

    trend_flags = build_summary_flags(series) if include_summary_flags else {}
    first_value = series[0]["value"] if series else None
    latest_value = series[-1]["value"] if series else None
    net_change_pct = None
    if first_value not in (None, 0) and latest_value is not None:
        first_float = float(cast(float | int | str, first_value))
        latest_float = float(cast(float | int | str, latest_value))
        net_change_pct = ((latest_float - first_float) / abs(first_float)) * 100.0

    sources = [item.get("source") for item in periods[-quarter_count:] if item.get("source")]

    return {
        "status": "OK" if series else "NOT_FOUND",
        "metric": metric,
        "currency": metric_payload.get("currency", "USD"),
        "unit": metric_payload.get("unit_map", {}).get(metric, "USD"),
        "series": series,
        "trend_flags": trend_flags,
        "summary_stats": {
            "latest_value": latest_value,
            "first_value": first_value,
            "net_change_pct": net_change_pct,
        },
        "sources": sources,
    }


def get_source_evidence(
    identifier: str,
    topic: str | None = None,
    metric: str | None = None,
    doc_type_hint: list[str] | None = None,
    limit: int = 3,
    max_chars_per_excerpt: int = 400,
) -> dict[str, Any]:
    if doc_type_hint is None:
        doc_type_hint = ["earnings_release", "earnings_call_transcript", "10-Q"]

    filings = get_recent_filings(identifier, doc_type_hint, limit=limit)
    if filings["status"] != "OK":
        return {"status": "NOT_FOUND", "evidence": []}

    search_terms: list[str] = []
    if topic == "guidance":
        search_terms.extend(["guidance", "outlook"])
    if metric:
        aliases = load_metric_aliases().get("metrics", {}).get(metric, {})
        search_terms.extend(aliases.get("aliases_en", []))
        search_terms.extend(aliases.get("aliases_ko", []))
    if not search_terms:
        search_terms = ["guidance"]

    evidence = []
    for filing in filings["items"]:
        bundle = docs_server.build_citation_bundle(
            document_id=filing["doc_id"], spans_or_sections=search_terms
        )
        for citation_item in bundle.data.get("citations", []):
            citation = citation_item["citation"]
            excerpt = citation.get("extracted_text", "")
            if not excerpt or excerpt == "[UNKNOWN]":
                continue
            evidence.append(
                {
                    "excerpt": excerpt[:max_chars_per_excerpt],
                    "topic": topic,
                    "document_type": filing["doc_type"],
                    "filing_date": filing["filing_date"],
                    "period_label": filing["period_label"],
                    "citation_text": f"{filing['filing_date']} {filing['doc_type']}",
                    "uri": filing["uri"],
                }
            )
            if len(evidence) >= limit:
                return {"status": "OK", "evidence": evidence}
    return {"status": "INSUFFICIENT_EVIDENCE", "evidence": evidence}

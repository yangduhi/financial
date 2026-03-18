"""SEC EDGAR-backed document gateway implementation."""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import requests
from bs4 import BeautifulSoup

from mcp.common.contracts import ToolResponseEnvelope
from mcp.common.errors import AmbiguousResultError, ConfigurationError, SourceUnavailableError
from mcp.common.provenance import CitationSpan, ProvenanceRecord
from mcp.common.runtime import load_project_env

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_BROWSE_EDGAR_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={company}&owner=exclude"
    "&count={count}&output=atom"
)
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik_nozeros}/{accession}/{filename}"


def _now() -> datetime:
    return datetime.now(UTC)


def _user_agent() -> str:
    load_project_env()
    user_agent = os.getenv("SEC_API_USER_AGENT") or os.getenv("SEC_USER_AGENT")
    if not user_agent:
        raise ConfigurationError(
            "SEC_API_USER_AGENT environment variable is required for SEC EDGAR requests."
        )
    return user_agent


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _user_agent(), "Accept-Encoding": "gzip, deflate"})
    return session


@lru_cache(maxsize=1)
def load_company_tickers() -> list[dict[str, Any]]:
    try:
        response = _session().get(SEC_COMPANY_TICKERS_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(f"Unable to fetch SEC company tickers: {exc}") from exc

    payload = response.json()
    return [payload[key] for key in payload]


def resolve_company(company_or_ticker: str) -> dict[str, Any]:
    query = company_or_ticker.strip().lower()
    records = load_company_tickers()
    matches = [
        record
        for record in records
        if record["ticker"].lower() == query
        or record["title"].lower() == query
        or query in record["title"].lower()
    ]
    if not matches:
        raise SourceUnavailableError(f"No SEC company match found for '{company_or_ticker}'.")
    exact_ticker = [record for record in matches if record["ticker"].lower() == query]
    if len(exact_ticker) == 1:
        return exact_ticker[0]
    if len(matches) > 1:
        raise AmbiguousResultError(f"Multiple SEC company matches found for '{company_or_ticker}'.")
    return matches[0]


def _browse_feed(company_or_ticker: str, count: int = 40) -> ET.Element:
    url = SEC_BROWSE_EDGAR_URL.format(company=company_or_ticker, count=count)
    try:
        response = _session().get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(
            f"Unable to fetch SEC browse feed for '{company_or_ticker}': {exc}"
        ) from exc
    return ET.fromstring(response.text)


def _recent_filings(company_record: dict[str, Any], count: int = 40) -> list[dict[str, Any]]:
    root = _browse_feed(company_record["ticker"], count=count)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    filings: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        category = entry.find("atom:category", ns)
        title = entry.findtext("atom:title", default="", namespaces=ns)
        updated = entry.findtext("atom:updated", default="", namespaces=ns)
        summary = entry.findtext("atom:summary", default="", namespaces=ns)
        link = entry.find("atom:link", ns)
        identifier = entry.findtext("atom:id", default="", namespaces=ns)
        accession_match = re.search(r"accession-number=([0-9-]+)", identifier)
        filed_match = re.search(r"Filed:</b>\s*([0-9-]+)", summary)
        accession = accession_match.group(1) if accession_match else ""
        filing_date = filed_match.group(1) if filed_match else updated[:10]
        filings.append(
            {
                "document_id": f"{company_record['cik_str']}:{accession}",
                "document_type": category.attrib.get("term", "") if category is not None else "",
                "issuer": company_record["title"],
                "published_at": filing_date,
                "title": title,
                "uri": link.attrib.get("href", "") if link is not None else "",
                "accession_number": accession,
            }
        )
    return filings


def _provenance(source_id: str, as_of_datetime: datetime | None = None) -> list[ProvenanceRecord]:
    return [
        ProvenanceRecord(
            source_id=source_id,
            source_type="document_source",
            source_system="sec_edgar_public",
            retrieved_at=_now(),
            as_of_datetime=as_of_datetime,
            license_scope="external_public",
            confidence=0.9,
            content_hash=source_id,
        )
    ]


def search_documents(
    query: str | None,
    company: str,
    date_range: tuple[str, str] | None = None,
    doc_types: list[str] | None = None,
    locale: str | None = None,
) -> ToolResponseEnvelope:
    del locale
    company_record = resolve_company(company)
    filings = _recent_filings(company_record)

    if doc_types:
        allowed = {doc_type.lower() for doc_type in doc_types}
        filings = [filing for filing in filings if filing["document_type"].lower() in allowed]

    if date_range:
        start, end = date_range
        filings = [filing for filing in filings if start <= filing["published_at"] <= end]

    if query:
        pattern = query.lower()
        filings = [
            filing
            for filing in filings
            if pattern in filing["title"].lower() or pattern in filing["document_type"].lower()
        ]

    return ToolResponseEnvelope(
        ok=True,
        data={
            "results": filings,
            "company": {
                "ticker": company_record["ticker"],
                "title": company_record["title"],
                "cik": company_record["cik_str"],
            },
        },
        provenance=_provenance(f"sec-browse-{company_record['cik_str']}"),
    )


def _parse_document_id(document_id: str) -> tuple[str, str]:
    cik, accession = document_id.split(":", 1)
    return cik, accession


def fetch_document(document_id: str) -> ToolResponseEnvelope:
    cik, accession = _parse_document_id(document_id)
    index_url = SEC_ARCHIVES_URL.format(
        cik_nozeros=str(int(cik)),
        accession=accession.replace("-", ""),
        filename=f"{accession}-index.htm",
    )
    try:
        index_response = _session().get(index_url, timeout=30)
        index_response.raise_for_status()
    except requests.RequestException as exc:
        raise SourceUnavailableError(
            f"Unable to fetch SEC document index '{document_id}': {exc}"
        ) from exc

    soup = BeautifulSoup(index_response.text, "html.parser")
    document_url = index_url
    for anchor in soup.find_all("a"):
        href_value = anchor.get("href")
        if not isinstance(href_value, str):
            continue
        href = href_value
        if href.endswith((".htm", ".html", ".txt")) and "-index" not in href:
            if href.startswith("/"):
                document_url = f"https://www.sec.gov{href}"
            else:
                document_url = SEC_ARCHIVES_URL.format(
                    cik_nozeros=str(int(cik)),
                    accession=accession.replace("-", ""),
                    filename=href,
                )
            break

    response = _session().get(document_url, timeout=30)
    response.raise_for_status()
    return ToolResponseEnvelope(
        ok=True,
        data={
            "document_id": document_id,
            "uri": document_url,
            "text": response.text,
            "content_type": response.headers.get("Content-Type", "text/html"),
        },
        provenance=_provenance(document_id),
    )


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_sections(document_id: str, sections: list[str]) -> ToolResponseEnvelope:
    document = fetch_document(document_id)
    normalized_text = _strip_html(document.data["text"])
    extracted: list[dict[str, str]] = []
    for section in sections:
        pattern = re.compile(re.escape(section), re.IGNORECASE)
        match = pattern.search(normalized_text)
        if not match:
            extracted.append({"section": section, "text": "[UNKNOWN]"})
            continue
        start = match.start()
        snippet = normalized_text[start : start + 1000].strip()
        extracted.append({"section": section, "text": snippet})

    return ToolResponseEnvelope(
        ok=True,
        data={"document_id": document_id, "sections": extracted},
        provenance=document.provenance,
    )


def get_latest_primary_sources(
    company_or_ticker: str, as_of_date: str | None = None
) -> ToolResponseEnvelope:
    response = search_documents(query=None, company=company_or_ticker)
    priority = {"8-K": 0, "10-Q": 1, "10-K": 2, "20-F": 3, "6-K": 4}
    filings = response.data["results"]
    if as_of_date:
        filings = [filing for filing in filings if filing["published_at"] <= as_of_date]
    filings.sort(
        key=lambda item: (priority.get(item["document_type"], 99), item["published_at"]),
        reverse=True,
    )
    return ToolResponseEnvelope(
        ok=True, data={"results": filings[:5]}, provenance=response.provenance
    )


def build_citation_bundle(document_id: str, spans_or_sections: list[str]) -> ToolResponseEnvelope:
    document = fetch_document(document_id)
    normalized_text = _strip_html(document.data["text"])
    citations: list[dict[str, Any]] = []
    provenance = document.provenance
    for item in spans_or_sections:
        pattern = re.compile(re.escape(item), re.IGNORECASE)
        match = pattern.search(normalized_text)
        if not match:
            citations.append(
                {
                    "section": item,
                    "citation": CitationSpan(
                        document_id=document_id,
                        page_or_section=item,
                        extracted_text="[UNKNOWN]",
                        parser_version="sec_edgar_v1",
                        confidence=0.0,
                    ).model_dump(mode="json"),
                }
            )
            continue
        start = max(match.start() - 150, 0)
        end = min(match.end() + 350, len(normalized_text))
        extracted_text = normalized_text[start:end].strip()
        citations.append(
            {
                "section": item,
                "citation": CitationSpan(
                    document_id=document_id,
                    page_or_section=item,
                    extracted_text=extracted_text,
                    parser_version="sec_edgar_v1",
                    confidence=0.75,
                ).model_dump(mode="json"),
            }
        )
    return ToolResponseEnvelope(
        ok=True,
        data={"document_id": document_id, "citations": citations},
        provenance=provenance,
    )

"""Document retrieval MCP gateway backed by SEC EDGAR."""

from __future__ import annotations

from dataclasses import dataclass

from . import sec_edgar


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str


DOCS_GATEWAY_TOOLS = [
    ToolDefinition("search_documents", "Search primary documents for an issuer or identifier."),
    ToolDefinition("fetch_document", "Fetch a single document by document_id."),
    ToolDefinition("extract_sections", "Extract structured sections from a document."),
    ToolDefinition(
        "get_latest_primary_sources",
        "Resolve the latest primary sources for a company."
    ),
    ToolDefinition("build_citation_bundle", "Build a citation bundle for downstream claims.")
]


def list_tools() -> list[ToolDefinition]:
    """Return the supported tools for the scaffold server."""

    return DOCS_GATEWAY_TOOLS


def search_documents(**kwargs):
    return sec_edgar.search_documents(**kwargs)


def fetch_document(**kwargs):
    return sec_edgar.fetch_document(**kwargs)


def extract_sections(**kwargs):
    return sec_edgar.extract_sections(**kwargs)


def get_latest_primary_sources(**kwargs):
    return sec_edgar.get_latest_primary_sources(**kwargs)


def build_citation_bundle(**kwargs):
    return sec_edgar.build_citation_bundle(**kwargs)

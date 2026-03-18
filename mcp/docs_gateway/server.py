"""Scaffold for the document retrieval MCP gateway."""

from __future__ import annotations

from dataclasses import dataclass


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

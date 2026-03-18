"""Shared exceptions for MCP gateways."""

from __future__ import annotations


class MCPError(Exception):
    """Base class for MCP-related failures."""


class ConfigurationError(MCPError):
    """Raised when required runtime configuration is missing."""


class AmbiguousResultError(MCPError):
    """Raised when an entity or document match is ambiguous."""


class EntitlementError(MCPError):
    """Raised when source usage is not allowed by entitlement or license."""


class SourceUnavailableError(MCPError):
    """Raised when an external source cannot be reached or is unavailable."""

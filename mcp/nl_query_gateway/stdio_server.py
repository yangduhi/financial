"""Minimal stdio MCP transport for the NL query gateway."""

from __future__ import annotations

import json
import sys
from typing import Any

from . import server as gateway

PROTOCOL_VERSION = "2025-11-25"
SERVER_INFO = {"name": "financial-nl-query-gateway", "version": "0.1.0"}

TOOLS = {
    "resolve_entity": {
        "name": "resolve_entity",
        "description": "Resolve a company expression into a canonical identifier.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "entity_type": {"type": "string"},
                "market_hint": {"type": "string"},
                "max_candidates": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    "get_quarterly_metrics": {
        "name": "get_quarterly_metrics",
        "description": "Return quarterly metric values and sources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "metrics": {"type": "array", "items": {"type": "string"}},
                "quarter_count": {"type": "integer"},
            },
            "required": ["identifier", "metrics"],
        },
    },
    "get_metric_trend": {
        "name": "get_metric_trend",
        "description": "Return structured trend data for a metric.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "metric": {"type": "string"},
                "quarter_count": {"type": "integer"},
            },
            "required": ["identifier", "metric"],
        },
    },
    "get_recent_filings": {
        "name": "get_recent_filings",
        "description": "Return recent filings or earnings documents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "doc_types": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer"},
            },
            "required": ["identifier", "doc_types"],
        },
    },
    "get_source_evidence": {
        "name": "get_source_evidence",
        "description": "Return grounded excerpts for a topic or metric.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "topic": {"type": ["string", "null"]},
                "metric": {"type": ["string", "null"]},
                "limit": {"type": "integer"},
            },
            "required": ["identifier"],
        },
    },
    "answer_query": {
        "name": "answer_query",
        "description": "Run the end-to-end natural-language query flow.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "persist": {"type": "boolean"},
            },
            "required": ["question"],
        },
    },
}


def _tool_result(payload: Any, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
        "structuredContent": payload,
        "isError": is_error,
    }


def _dispatch_tool(name: str, args: dict[str, Any]) -> Any:
    if name == "resolve_entity":
        return gateway.resolve_entity_tool(**args)
    if name == "get_quarterly_metrics":
        return gateway.get_quarterly_metrics_tool(**args)
    if name == "get_metric_trend":
        return gateway.get_metric_trend_tool(**args)
    if name == "get_recent_filings":
        return gateway.get_recent_filings_tool(**args)
    if name == "get_source_evidence":
        return gateway.get_source_evidence_tool(**args)
    if name == "answer_query":
        return gateway.answer_query(**args)
    raise KeyError(name)


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": list(TOOLS.values())}}

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            payload = _dispatch_tool(name, arguments)
            return {"jsonrpc": "2.0", "id": request_id, "result": _tool_result(payload)}
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": _tool_result({"error": str(exc), "tool": name}, is_error=True),
            }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def _read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        key, value = line.decode("utf-8").split(":", 1)
        headers[key.strip()] = value.strip()

    length = int(headers.get("Content-Length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode())
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def main() -> None:
    while True:
        message = _read_message()
        if message is None:
            break
        response = handle_request(message)
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    main()

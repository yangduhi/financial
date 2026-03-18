from datetime import datetime

from mcp.common.contracts import RequestContext, ToolResponseEnvelope
from mcp.common.provenance import ProvenanceRecord


def test_request_context_requires_ids() -> None:
    context = RequestContext(
        request_id="req-1",
        trace_id="trace-1",
        requester="codex",
        team="research",
        purpose="test",
        requested_at=datetime(2026, 3, 18)
    )
    assert context.request_id == "req-1"


def test_response_envelope_accepts_provenance() -> None:
    provenance = ProvenanceRecord(
        source_id="src-1",
        source_type="document",
        source_system="placeholder",
        retrieved_at=datetime(2026, 3, 18),
        as_of_datetime=datetime(2026, 3, 18),
        license_scope="external_public",
        confidence=0.9,
        content_hash="abc123"
    )
    envelope = ToolResponseEnvelope(ok=True, provenance=[provenance])
    assert envelope.ok is True

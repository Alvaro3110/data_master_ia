import uuid

from app.main import _resolve_trace_id


def test_resolve_trace_id_keeps_valid_uuid() -> None:
    provided = str(uuid.uuid4())
    assert _resolve_trace_id(provided) == provided


def test_resolve_trace_id_replaces_invalid_uuid() -> None:
    resolved = _resolve_trace_id("trace-invalido")
    assert resolved != "trace-invalido"
    uuid.UUID(resolved)

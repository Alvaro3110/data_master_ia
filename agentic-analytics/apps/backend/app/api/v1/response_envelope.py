"""Helpers para envelope padrão `{trace_id, data}`."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


def get_trace_id(request: Request | None = None) -> str:
    if request is not None:
        trace_id = getattr(request.state, "trace_id", None)
        if trace_id:
            return trace_id
    return str(uuid4())


def envelope_payload(data: Any, request: Request | None = None, trace_id: str | None = None) -> dict[str, Any]:
    resolved_trace_id = trace_id or get_trace_id(request)
    return {
        "trace_id": resolved_trace_id,
        "data": data,
    }


def envelope_response(
    data: Any,
    request: Request | None = None,
    status_code: int = 200,
    trace_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=envelope_payload(data=data, request=request, trace_id=trace_id),
    )

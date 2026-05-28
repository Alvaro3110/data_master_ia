"""GET /api/v1/traces/{trace_id} — consulta de trace."""
from fastapi import APIRouter, HTTPException, Request
from app.api.v1.response_envelope import envelope_response
router = APIRouter()

@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str, request: Request):
    try:
        import duckdb
        from pathlib import Path
        from app.config import settings
        db_path = Path(settings.DUCKDB_PATH)
        if not db_path.exists():
            raise FileNotFoundError
        with duckdb.connect(str(db_path), read_only=True) as conn:
            result = conn.execute(
                "SELECT * FROM query_audit_log WHERE trace_id = ? LIMIT 1", [trace_id]
            ).fetchdf()
        if result.empty:
            raise HTTPException(status_code=404, detail="Trace not found")
        return envelope_response(result.to_dict("records")[0], request=request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Trace not found: {str(e)}")

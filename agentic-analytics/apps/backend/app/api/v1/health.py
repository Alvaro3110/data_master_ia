"""Health check endpoint — padrão Week3-7."""
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Verifica saúde de todos os serviços.
    Padrão: Week3 usa /api/v1/health como referência de healthcheck.
    """
    services = {}

    # OpenSearch
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OPENSEARCH_HOST}/_cluster/health")
            status = resp.json().get("status", "unknown")
            services["opensearch"] = {"status": "healthy" if status in ("green", "yellow") else "degraded", "detail": status}
    except Exception as e:
        services["opensearch"] = {"status": "unhealthy", "detail": str(e)}

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_HOST}/api/version")
            services["ollama"] = {"status": "healthy" if resp.status_code == 200 else "unhealthy"}
    except Exception as e:
        services["ollama"] = {"status": "unhealthy", "detail": str(e)}

    # PostgreSQL — via SQLAlchemy ping
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(settings.POSTGRES_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        services["postgres"] = {"status": "healthy"}
    except Exception as e:
        services["postgres"] = {"status": "unhealthy", "detail": str(e)}

    all_ok = all(s.get("status") in ("healthy", "degraded") for s in services.values())

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok" if all_ok else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services,
            "version": "0.1.0",
        },
    )

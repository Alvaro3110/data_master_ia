"""
FastAPI Application — Agentic Analytics para Pricing/Margem/Safra/Risco/ROAE
Padrão: Week3-7 do production-agentic-rag-course + LangGraph Week7
"""
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import health, ask_analytics, search_rules, traces, workspaces
from app.api.v1.response_envelope import envelope_payload
from app.config import settings
from app.db.session import init_db


def _resolve_trace_id(raw_trace_id: str | None) -> str:
    """Aceita trace recebido apenas se for UUID válido; caso contrário, gera novo."""
    if not raw_trace_id:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(raw_trace_id.strip()))
    except (ValueError, AttributeError):
        return str(uuid.uuid4())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print(f"🚀 Agentic Analytics API starting — env={settings.APP_ENV}")
    try:
        init_db()
        print("✅ Database schemas initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database schemas: {e}")
    yield
    print("🛑 API shutting down")


app = FastAPI(
    title="Agentic Analytics — Pricing & Risco",
    description="Plataforma analítica conversacional governada para pricing, margem, safra, risco e ROAE.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Tracing Middleware ───────────────────────────────────────────────────────
@app.middleware("http")
async def inject_trace_id(request: Request, call_next):
    """Injeta trace_id em toda request e adiciona ao response header."""
    trace_id = _resolve_trace_id(request.headers.get("X-Trace-ID"))
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response


# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(ask_analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(search_rules.router, prefix="/api/v1", tags=["rag"])
app.include_router(traces.router, prefix="/api/v1", tags=["observability"])
app.include_router(workspaces.router)


# ─── Exception handlers ──────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope_payload({"detail": exc.detail}, request=request),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=envelope_payload({"detail": exc.errors()}, request=request),
    )


# ─── Root ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root(request: Request):
    return envelope_payload({
        "service": "Agentic Analytics API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/api/v1/health",
    }, request=request)

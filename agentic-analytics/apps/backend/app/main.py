"""
FastAPI Application — Agentic Analytics para Pricing/Margem/Safra/Risco/ROAE
Padrão: Week3-7 do production-agentic-rag-course + LangGraph Week7
"""
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import health, ask_analytics, search_rules, traces, workspaces
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print(f"🚀 Agentic Analytics API starting — env={settings.APP_ENV}")
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
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
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


# ─── Root ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "Agentic Analytics API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/api/v1/health",
    }

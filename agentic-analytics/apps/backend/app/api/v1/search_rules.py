"""POST /api/v1/search-rules — busca no RAG de regras."""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.agent.rag_agent import search_rules as _search
from app.api.v1.response_envelope import envelope_payload

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/search-rules")
async def search_rules(body: SearchRequest, request: Request):
    chunks, sources = _search(body.query, top_k=body.top_k)
    return envelope_payload({
        "query": body.query,
        "chunks": chunks,
        "sources": sources,
        "total": len(chunks),
    }, request=request)

"""
RAG Agent — Fase 1: busca híbrida OpenSearch (60% BM25 + 40% vector).
Padrão: Week3 (BM25) + Week4 (Jina embeddings + hybrid search).
Separação correta: task='retrieval.query' para queries, 'retrieval.passage' para indexação.
Fallback: busca local nos arquivos markdown de data/docs/.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Peso híbrido: 60% BM25 + 40% vector (Week 4 pattern)
BM25_WEIGHT = 0.60
VECTOR_WEIGHT = 0.40

# Dimensão dos embeddings Jina v3
JINA_EMBEDDING_DIM = 1024


# ── Resultado ────────────────────────────────────────────────────────────────

@dataclass
class RagResult:
    """Resultado da busca RAG híbrida."""
    chunks: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    used_fallback: bool = False
    scores: list[float] = field(default_factory=list)


# ── Agente ───────────────────────────────────────────────────────────────────

class RagAgent:
    """
    Agente RAG com busca híbrida OpenSearch.
    - BM25 (keyword): 60% do score final.
    - Vector (knn): 40% do score final.
    - Embeddings via Jina com task='retrieval.query' para queries.
    - Fallback local para arquivos markdown quando OpenSearch está indisponível.
    """

    def _get_embedding(self, text: str, task: str = "retrieval.passage") -> list[float]:
        """
        Gera embedding via Jina API ou OpenAI API.
        IMPORTANTE: usar task='retrieval.query' para perguntas do usuário,
        e task='retrieval.passage' para documentos indexados.
        """
        if settings.has_jina_key:
            try:
                resp = httpx.post(
                    "https://api.jina.ai/v1/embeddings",
                    headers={"Authorization": f"Bearer {settings.JINA_API_KEY}"},
                    json={"model": settings.JINA_MODEL, "task": task, "input": [text]},
                    timeout=10.0,
                )
                resp.raise_for_status()
                return resp.json()["data"][0]["embedding"]
            except Exception as e:
                logger.warning(f"Jina API falhou: {e} — caindo para outros provedores")

        if settings.has_openai_key:
            try:
                resp = httpx.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={"model": "text-embedding-3-small", "dimensions": JINA_EMBEDDING_DIM, "input": [text]},
                    timeout=10.0,
                )
                resp.raise_for_status()
                return resp.json()["data"][0]["embedding"]
            except Exception as e:
                logger.warning(f"OpenAI Embeddings falhou: {e} — caindo para sentence-transformers")

        # Fallback: sentence-transformers local
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            vec = model.encode(text).tolist()
            # Padeia ou trunca para o tamanho esperado
            if len(vec) < JINA_EMBEDDING_DIM:
                vec = vec + [0.0] * (JINA_EMBEDDING_DIM - len(vec))
            return vec[:JINA_EMBEDDING_DIM]
        except Exception as e:
            logger.error(f"sentence-transformers falhou: {e}")
            return [0.0] * JINA_EMBEDDING_DIM

    def _get_opensearch_client(self):
        """Cria cliente OpenSearch."""
        from opensearchpy import OpenSearch
        return OpenSearch(
            hosts=[settings.OPENSEARCH_HOST],
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
            timeout=5,
        )

    def _bm25_search(self, question: str, top_k: int) -> list[dict]:
        """Busca BM25 (keyword) no OpenSearch."""
        client = self._get_opensearch_client()
        query = {
            "query": {
                "multi_match": {
                    "query": question,
                    "fields": ["titulo^2", "texto"],
                    "type": "best_fields",
                }
            },
            "size": top_k,
        }
        resp = client.search(index=settings.OPENSEARCH_INDEX_RULES, body=query)
        return resp["hits"]["hits"]

    def _vector_search(self, embedding: list[float], top_k: int) -> list[dict]:
        """Busca vetorial (knn) no OpenSearch."""
        client = self._get_opensearch_client()
        query = {
            "query": {
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": top_k,
                    }
                }
            },
            "size": top_k,
        }
        resp = client.search(index=settings.OPENSEARCH_INDEX_RULES, body=query)
        return resp["hits"]["hits"]

    def _merge_hybrid(
        self,
        bm25_hits: list[dict],
        vector_hits: list[dict],
        top_k: int,
    ) -> list[dict]:
        """
        Combina resultados BM25 e vector com ponderação 60/40.
        Normaliza scores de cada lista para [0, 1] antes de combinar.
        Deduplica por source_url.
        """
        scores: dict[str, float] = {}
        docs: dict[str, dict] = {}

        # Normaliza BM25
        bm25_max = max((h["_score"] for h in bm25_hits), default=1.0) or 1.0
        for hit in bm25_hits:
            src = hit["_source"]
            key = src.get("source_url", src.get("titulo", ""))
            norm_score = (hit["_score"] / bm25_max) * BM25_WEIGHT
            scores[key] = scores.get(key, 0.0) + norm_score
            docs[key] = src

        # Normaliza vector
        vec_max = max((h["_score"] for h in vector_hits), default=1.0) or 1.0
        for hit in vector_hits:
            src = hit["_source"]
            key = src.get("source_url", src.get("titulo", ""))
            norm_score = (hit["_score"] / vec_max) * VECTOR_WEIGHT
            scores[key] = scores.get(key, 0.0) + norm_score
            docs[key] = src

        # Ordena por score combinado e retorna top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"_source": docs[k], "_score": v} for k, v in ranked]

    def search_rules(self, question: str, top_k: int = 3) -> RagResult:
        """
        Busca híbrida: BM25 (60%) + vector (40%) no OpenSearch.
        Fallback local em data/docs/ se OpenSearch estiver indisponível.
        """
        if not question.strip():
            return RagResult()

        try:
            # Embedding com task correto para query
            embedding = self._get_embedding(question, task="retrieval.query")

            bm25_hits = self._bm25_search(question, top_k=top_k * 2)
            vector_hits = self._vector_search(embedding, top_k=top_k * 2)

            merged = self._merge_hybrid(bm25_hits, vector_hits, top_k=top_k)

            chunks, sources, scores = [], [], []
            for item in merged:
                src = item["_source"]
                chunks.append(f"[{src.get('titulo', 'Doc')}]\n{src.get('texto', '')}")
                sources.append(src.get("source_url", src.get("titulo", "unknown")))
                scores.append(item["_score"])

            return RagResult(chunks=chunks, sources=sources, scores=scores, used_fallback=False)

        except Exception as e:
            logger.warning(f"OpenSearch indisponível: {e} — usando fallback local")
            return self._fallback_file_search(question, top_k)

    def _fallback_file_search(self, question: str, top_k: int) -> RagResult:
        """Fallback: busca por palavras-chave nos arquivos markdown locais."""
        docs_dir = (
            Path(__file__).parent.parent.parent.parent.parent / "data" / "docs"
        )
        chunks, sources = [], []
        q_lower = question.lower()

        if docs_dir.exists():
            for md_file in sorted(docs_dir.glob("*.md")):
                text = md_file.read_text(encoding="utf-8")
                if any(word in text.lower() for word in q_lower.split()[:5]):
                    chunks.append(text[:1500])
                    sources.append(md_file.name)
                    if len(chunks) >= top_k:
                        break

        return RagResult(chunks=chunks, sources=sources, used_fallback=True)


# ── Backward-compat ───────────────────────────────────────────────────────────

_default_agent = RagAgent()


def search_rules(question: str, top_k: int = 3) -> tuple[list[str], list[str]]:
    """Wrapper funcional para compatibilidade com o graph.py atual."""
    result = _default_agent.search_rules(question, top_k=top_k)
    return result.chunks, result.sources

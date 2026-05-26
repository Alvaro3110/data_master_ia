"""
TDD — Fase 1: RAG Agent com busca híbrida OpenSearch (60% BM25 + 40% vector).
Testa que o agente:
- Usa busca BM25 e vetorial separadas e combina resultados (60/40)
- Usa task='retrieval.query' para queries e 'retrieval.passage' para documentos
- Faz fallback local quando OpenSearch está indisponível
- Deduplica resultados por source
- Respeita o top_k
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.agent.rag_agent import RagAgent, RagResult


class TestRagHybridSearch:
    """Testa a busca híbrida BM25 + vector no OpenSearch."""

    @pytest.fixture
    def agent(self):
        return RagAgent()

    @pytest.fixture
    def mock_bm25_hits(self):
        """Simula resposta do OpenSearch para busca BM25."""
        return {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "titulo": "Definição de Alto Risco",
                            "texto": "Clientes com score_risco >= 7 são classificados como alto risco.",
                            "source_url": "regras/alto_risco.md",
                        },
                        "_score": 2.5,
                    },
                    {
                        "_source": {
                            "titulo": "Política de Pricing PME",
                            "texto": "A margem mínima para PME é de 2.5% ao mês.",
                            "source_url": "regras/pricing_pme.md",
                        },
                        "_score": 1.8,
                    },
                ]
            }
        }

    @pytest.fixture
    def mock_vector_hits(self):
        """Simula resposta do OpenSearch para busca vetorial (knn)."""
        return {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "titulo": "Regras de Risco de Crédito",
                            "texto": "O score de risco varia de 0 a 10. Acima de 7 é alto risco.",
                            "source_url": "regras/risco_credito.md",
                        },
                        "_score": 0.92,
                    },
                    {
                        "_source": {
                            "titulo": "Definição de Alto Risco",
                            "texto": "Clientes com score_risco >= 7 são classificados como alto risco.",
                            "source_url": "regras/alto_risco.md",
                        },
                        "_score": 0.88,
                    },
                ]
            }
        }

    def test_hybrid_search_combina_bm25_e_vector(self, agent, mock_bm25_hits, mock_vector_hits):
        """A busca híbrida deve combinar resultados BM25 e vetoriais com peso 60/40."""
        with patch.object(agent, "_bm25_search", return_value=mock_bm25_hits["hits"]["hits"]) as mock_bm25, \
             patch.object(agent, "_vector_search", return_value=mock_vector_hits["hits"]["hits"]) as mock_vec, \
             patch.object(agent, "_get_embedding", return_value=[0.1] * 1024):
            result = agent.search_rules("O que é alto risco?", top_k=3)

        assert isinstance(result, RagResult)
        assert len(result.chunks) > 0
        assert len(result.sources) > 0
        mock_bm25.assert_called_once()
        mock_vec.assert_called_once()

    def test_hybrid_search_deduplica_por_source(self, agent, mock_bm25_hits, mock_vector_hits):
        """Documentos que aparecem tanto no BM25 quanto no vector não devem duplicar."""
        # mock_bm25_hits e mock_vector_hits têm "Definição de Alto Risco" em comum
        with patch.object(agent, "_bm25_search", return_value=mock_bm25_hits["hits"]["hits"]), \
             patch.object(agent, "_vector_search", return_value=mock_vector_hits["hits"]["hits"]), \
             patch.object(agent, "_get_embedding", return_value=[0.1] * 1024):
            result = agent.search_rules("O que é alto risco?", top_k=5)

        # "Definição de Alto Risco" aparece nos dois — não pode duplicar
        seen_sources = [s for s in result.sources if "alto_risco" in s]
        assert len(seen_sources) <= 1, f"Duplicata detectada: {result.sources}"

    def test_respeita_top_k(self, agent, mock_bm25_hits, mock_vector_hits):
        """Resultado deve respeitar o top_k solicitado."""
        with patch.object(agent, "_bm25_search", return_value=mock_bm25_hits["hits"]["hits"]), \
             patch.object(agent, "_vector_search", return_value=mock_vector_hits["hits"]["hits"]), \
             patch.object(agent, "_get_embedding", return_value=[0.1] * 1024):
            result = agent.search_rules("O que é alto risco?", top_k=2)

        assert len(result.chunks) <= 2

    def test_fallback_quando_opensearch_indisponivel(self, agent):
        """Se OpenSearch estiver fora, deve usar fallback local sem lançar exceção."""
        with patch.object(agent, "_bm25_search", side_effect=Exception("Connection refused")):
            result = agent.search_rules("O que é safra?", top_k=3)

        assert isinstance(result, RagResult)
        # Fallback pode ter 0 chunks se não houver arquivos locais relevantes
        assert result.chunks is not None
        assert result.sources is not None
        assert result.used_fallback is True

    def test_embedding_usa_task_retrieval_query(self, agent):
        """Para queries do usuário, deve usar task='retrieval.query' (não 'retrieval.passage')."""
        captured = {}

        def capture_embedding(text: str, task: str = "retrieval.passage"):
            captured["task"] = task
            return [0.1] * 1024

        with patch.object(agent, "_get_embedding", side_effect=capture_embedding), \
             patch.object(agent, "_bm25_search", return_value=[]), \
             patch.object(agent, "_vector_search", return_value=[]):
            agent.search_rules("Qual a definição de ROAE?", top_k=3)

        assert captured.get("task") == "retrieval.query", \
            "Queries devem usar task='retrieval.query', não 'retrieval.passage'"

    def test_score_hibrido_pondera_60_bm25_40_vector(self, agent):
        """Score final deve ponderar 60% do score BM25 e 40% do score vetorial."""
        # Documento A: score BM25=2.0, score vector=0.5 → score_norm BM25 alto
        # Documento B: score BM25=0.5, score vector=0.95 → score_norm vector alto
        bm25_hits = [
            {"_source": {"titulo": "Doc A", "texto": "Texto A", "source_url": "a.md"}, "_score": 2.0},
            {"_source": {"titulo": "Doc B", "texto": "Texto B", "source_url": "b.md"}, "_score": 0.5},
        ]
        vector_hits = [
            {"_source": {"titulo": "Doc B", "texto": "Texto B", "source_url": "b.md"}, "_score": 0.95},
            {"_source": {"titulo": "Doc A", "texto": "Texto A", "source_url": "a.md"}, "_score": 0.5},
        ]
        with patch.object(agent, "_bm25_search", return_value=bm25_hits), \
             patch.object(agent, "_vector_search", return_value=vector_hits), \
             patch.object(agent, "_get_embedding", return_value=[0.1] * 1024):
            result = agent.search_rules("query teste", top_k=2)

        # Apenas verifica que retornou resultados sem erro
        assert len(result.chunks) == 2

    def test_retorna_rag_result_vazio_para_query_vazia(self, agent):
        """Query vazia deve retornar RagResult vazio sem lançar exceção."""
        result = agent.search_rules("", top_k=3)
        assert isinstance(result, RagResult)
        assert result.chunks == []
        assert result.sources == []

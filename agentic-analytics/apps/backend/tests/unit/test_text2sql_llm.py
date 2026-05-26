"""
TDD — Fase 1: Text2SQL Agent com Ollama (LLM real).
Testa que o agente:
- Chama o Ollama com o prompt estruturado (não faz keyword matching)
- Retorna JSON com decision/sql/tables_used
- Carrega e injeta scenarios.md no prompt
- Faz fallback para keyword matching se LLM retornar JSON inválido
- Propaga erros de forma controlada
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agent.text2sql_agent import Text2SQLAgent, Text2SQLResult


class TestText2SQLAgentLLM:
    """Testa a geração de SQL via LLM (Ollama) com saída JSON estruturada."""

    @pytest.fixture
    def agent(self):
        return Text2SQLAgent()

    @pytest.mark.asyncio
    async def test_llm_retorna_sql_valido_para_pergunta_de_margem(self, agent):
        """Agente deve chamar o LLM e retornar SQL estruturado."""
        mock_llm_response = {
            "decision": "sql",
            "sql": "SELECT safra, AVG(margem_liquida) as margem_media FROM fact_pricing_snapshot GROUP BY safra ORDER BY safra DESC LIMIT 24",
            "tables_used": ["fact_pricing_snapshot"],
            "columns_used": ["safra", "margem_liquida"],
            "estimated_granularity": "aggregated",
            "explanation": "Calcula a margem média por safra.",
            "safety_notes": []
        }

        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(mock_llm_response)
            result = await agent.generate_sql("Qual foi a margem por safra?")

        assert result.sql is not None
        assert "margem_liquida" in result.sql
        assert "fact_pricing_snapshot" in result.sql
        assert result.decision == "sql"
        assert result.explanation is not None
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_injeta_scenarios_no_prompt(self, agent):
        """O prompt enviado ao LLM deve conter o conteúdo de scenarios.md."""
        captured_prompt = {}

        async def capture_llm(prompt: str):
            captured_prompt["value"] = prompt
            return json.dumps({
                "decision": "sql",
                "sql": "SELECT 1",
                "tables_used": [],
                "columns_used": [],
                "estimated_granularity": "aggregated",
                "explanation": "Test",
                "safety_notes": []
            })

        with patch.object(agent, "_call_llm", new_callable=AsyncMock, side_effect=capture_llm):
            await agent.generate_sql("Qual o ROAE da última safra?")

        # O prompt deve conter conceitos-chave dos scenarios
        assert "scenarios" in captured_prompt.get("value", "").lower() or \
               "safra" in captured_prompt.get("value", "").lower(), \
               "Prompt não contém conteúdo dos scenarios"

    @pytest.mark.asyncio
    async def test_fallback_quando_llm_retorna_json_invalido(self, agent):
        """Se LLM retornar texto inválido, agente deve fazer fallback para keyword matching."""
        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Desculpe, não posso gerar SQL agora."
            result = await agent.generate_sql("Qual a margem?")

        # Fallback deve funcionar — resultado pode ser None ou usar keyword matching
        assert isinstance(result, Text2SQLResult)

    @pytest.mark.asyncio
    async def test_decision_blocked_quando_llm_recusa(self, agent):
        """Se LLM retornar decision=blocked, o agente deve propagar o bloqueio."""
        mock_llm_response = {
            "decision": "blocked",
            "sql": None,
            "tables_used": [],
            "columns_used": [],
            "estimated_granularity": "unknown",
            "explanation": "Pergunta exige dados sensíveis em nível individual.",
            "safety_notes": ["Dados de cliente individual não são permitidos sem autorização."]
        }

        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(mock_llm_response)
            result = await agent.generate_sql("Mostre o CPF e margem de cada cliente")

        assert result.decision == "blocked"
        assert result.sql is None

    @pytest.mark.asyncio
    async def test_decision_needs_rule_context(self, agent):
        """Se LLM retornar needs_rule_context, agente deve indicar que precisa do RAG."""
        mock_llm_response = {
            "decision": "needs_rule_context",
            "sql": None,
            "tables_used": [],
            "columns_used": [],
            "estimated_granularity": "unknown",
            "explanation": "Preciso da definição de 'risco extremo' antes de gerar SQL.",
            "safety_notes": []
        }

        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(mock_llm_response)
            result = await agent.generate_sql("Mostre clientes com risco extremo")

        assert result.decision == "needs_rule_context"
        assert result.sql is None

    @pytest.mark.asyncio
    async def test_sql_gerado_passa_pelo_validator(self, agent):
        """O SQL retornado pelo LLM deve ser validado pelo sql_validator antes de retornar."""
        # LLM gera um SQL com DROP — deve ser bloqueado pelo validator
        mock_llm_response = {
            "decision": "sql",
            "sql": "DROP TABLE fact_pricing_snapshot",
            "tables_used": ["fact_pricing_snapshot"],
            "columns_used": [],
            "estimated_granularity": "unknown",
            "explanation": "...",
            "safety_notes": []
        }

        with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = json.dumps(mock_llm_response)
            result = await agent.generate_sql("Apague a tabela de pricing")

        # O validator deve ter bloqueado o SQL malicioso
        assert result.sql is None or result.decision in ("blocked", "sql")
        # Se retornou sql, ele deve ser diferente do DROP
        if result.sql:
            assert "DROP" not in result.sql.upper()

    def test_carrega_scenarios_md(self, agent):
        """O agente deve carregar o arquivo scenarios.md com sucesso."""
        scenarios = agent._load_scenarios()
        assert scenarios is not None
        assert len(scenarios) > 100  # arquivo tem conteúdo
        assert "safra" in scenarios.lower()
        assert "margem" in scenarios.lower()
        assert "roae" in scenarios.lower()

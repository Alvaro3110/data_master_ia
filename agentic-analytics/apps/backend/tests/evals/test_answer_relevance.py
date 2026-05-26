"""
TDD — Fase 5: Avaliação Contínua.
Testes que utilizam LLM-as-a-judge para avaliar a relevância da resposta em relação à pergunta.
(LangSmith offline/local)
"""
import pytest


class TestAnswerRelevance:
    
    @pytest.mark.asyncio
    async def test_relevance_evaluator_judge(self):
        """O LLM-as-a-judge deve classificar uma resposta correta como RELEVANTE."""
        from app.agent.evaluators import evaluate_relevance
        
        question = "Qual a margem da safra?"
        answer = "A margem apurada para a safra atual é de 4.2%."
        
        result = await evaluate_relevance(question, answer)
        assert result["score"] >= 0.6
        assert result["is_relevant"] is True

    @pytest.mark.asyncio
    async def test_relevance_evaluator_judge_fails_bad_answer(self):
        """O LLM-as-a-judge deve classificar uma resposta irrelevante como NÃO RELEVANTE."""
        from app.agent.evaluators import evaluate_relevance
        
        question = "Qual a margem da safra?"
        answer = "A pizza é muito boa."
        
        result = await evaluate_relevance(question, answer)
        assert result["score"] < 0.5
        assert result["is_relevant"] is False

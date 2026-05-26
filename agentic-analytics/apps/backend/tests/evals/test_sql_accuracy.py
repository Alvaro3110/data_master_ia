"""
TDD — Fase 5: Avaliação Contínua.
Testes que utilizam heurísticas ou LLM-as-a-judge para avaliar a acurácia de uma query SQL gerada.
"""
import pytest


class TestSQLAccuracy:
    
    def test_sql_accuracy_evaluator_validates_columns(self):
        """O avaliador deve checar se a query referencia tabelas/colunas corretas."""
        from app.agent.evaluators import evaluate_sql_accuracy
        
        question = "Qual a margem da safra?"
        generated_sql = "SELECT margem FROM pricing_data WHERE safra = '2026-03'"
        expected_tables = ["pricing_data"]
        
        result = evaluate_sql_accuracy(question, generated_sql, expected_tables)
        assert result["score"] >= 0.8
        assert result["is_accurate"] is True

    def test_sql_accuracy_evaluator_fails_wrong_tables(self):
        """O avaliador deve falhar se a query faz referência a tabelas proibidas/inexistentes."""
        from app.agent.evaluators import evaluate_sql_accuracy
        
        question = "Qual a margem?"
        generated_sql = "SELECT * FROM users_passwords"
        expected_tables = ["pricing_data"]
        
        result = evaluate_sql_accuracy(question, generated_sql, expected_tables)
        assert result["score"] < 0.5
        assert result["is_accurate"] is False

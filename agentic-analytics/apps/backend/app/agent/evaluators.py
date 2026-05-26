"""
Avaliadores Contínuos (LLM-as-a-judge & Heurísticas) — Fase 5
Utilizados para validar qualidade das respostas em CI/CD (LangSmith Evals).
"""
import json
import httpx
from app.config import settings


async def evaluate_relevance(question: str, answer: str) -> dict:
    """
    Usa LLM-as-a-judge para classificar se a resposta atende à pergunta.
    """
    prompt = f"""
    Você é um juiz avaliando a relevância de uma resposta de um sistema analítico financeiro.
    Pergunta: {question}
    Resposta: {answer}
    
    A resposta resolve a pergunta de forma satisfatória?
    Responda APENAS com um JSON contendo 'score' (0.0 a 1.0) e 'justification'.
    Exemplo: {{"score": 0.9, "justification": "Boa resposta"}}
    """
    
    try:
        from app.services.llm_provider import generate_response
        content = await generate_response(prompt=prompt, model=settings.OLLAMA_MODEL)
        data = json.loads(content)
        score = float(data.get("score", 0.0))
        return {
            "score": score,
            "is_relevant": score >= 0.8,
            "justification": data.get("justification", "")
        }
    except Exception as e:
        # Fallback de heurística burra se falhar o LLM
        import re
        q_clean = re.sub(r'[^\w\s]', '', question.lower())
        a_clean = re.sub(r'[^\w\s]', '', answer.lower())
        q_words = set(q_clean.split())
        a_words = set(a_clean.split())
        overlap = len(q_words.intersection(a_words))
        score = min(1.0, overlap / max(1, len(q_words)))
        return {
            "score": score,
            "is_relevant": score >= 0.5,
            "justification": f"Fallback eval error: {e}"
        }


def evaluate_sql_accuracy(question: str, generated_sql: str, expected_tables: list[str]) -> dict:
    """
    Valida heuristicamente (ou via LLM) se o SQL usa as tabelas corretas e é seguro.
    """
    sql_lower = generated_sql.lower()
    
    # Heurística: Checa tabelas esperadas
    tables_found = [t for t in expected_tables if t.lower() in sql_lower]
    
    # Heurística: Checa tabelas proibidas
    forbidden = ["users", "passwords", "credentials", "secrets"]
    has_forbidden = any(f in sql_lower for f in forbidden)
    
    if has_forbidden:
        return {
            "score": 0.0,
            "is_accurate": False,
            "justification": "SQL acessa tabelas proibidas."
        }
        
    if not tables_found:
        return {
            "score": 0.2,
            "is_accurate": False,
            "justification": "SQL não referencia as tabelas esperadas."
        }
        
    return {
        "score": 1.0,
        "is_accurate": True,
        "justification": "SQL aparenta estar correto e seguro."
    }

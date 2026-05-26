"""
Provider central de LLM.
Fase 2.5: Isolamento da responsabilidade de integração externa com LLM,
com retries, logs centralizados e padronização de host.
"""
import logging
from app.services.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    pass


# Instância padrão global para manter compatibilidade com importações antigas
_provider = LLMProvider()


async def generate_response(prompt: str, model: str = "llama3") -> str:
    """
    Invoca o LLM. Usa o LLMProvider centralizado que gerencia OpenAI e Ollama fallback.
    """
    try:
        result = await _provider.generate(prompt)
        return result.text
    except Exception as e:
        logger.error(f"Erro ao gerar resposta no LLM: {e}")
        raise LLMProviderError(f"LLM generation failed: {e}") from e

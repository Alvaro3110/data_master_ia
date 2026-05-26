"""
Provider central de LLM.
Fase 2.5: Isolamento da responsabilidade de integração externa com LLM,
com retries, logs centralizados e padronização de host.
"""
import httpx
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    pass


def should_retry(retry_state):
    """Lógica customizada para decidir se tentamos de novo."""
    return True


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, LLMProviderError)),
    reraise=True
)
async def generate_response(prompt: str, model: str = "llama3") -> str:
    """
    Invoca o LLM. Usa OpenAI se a chave estiver configurada,
    caso contrário faz fallback para o Ollama local.
    """
    if settings.has_openai_key:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            chat = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)
            msg = await chat.ainvoke([HumanMessage(content=prompt)])
            return msg.content
        except ImportError:
            logger.error("langchain_openai não instalado, fazendo fallback para Ollama.")
        except Exception as e:
            logger.error(f"Erro na API da OpenAI: {e}")
            raise LLMProviderError(f"OpenAI error: {e}") from e

    url = f"{settings.OLLAMA_HOST}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.HTTPError as e:
        logger.error(f"Erro ao acessar LLM ({url}): {e}")
        raise LLMProviderError(f"LLM connection error: {e}") from e

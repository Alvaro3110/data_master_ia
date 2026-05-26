import pytest
from unittest.mock import AsyncMock, patch
from app.config import settings
from app.agent.text2sql_agent import Text2SQLAgent


@pytest.mark.asyncio
async def test_text2sql_usa_host_configurado_do_settings():
    """
    Garante que o Text2SQLAgent usa a variável oficial OLLAMA_HOST,
    e não uma variável fantasma (como OLLAMA_BASE_URL).
    """
    agent = Text2SQLAgent()

    from unittest.mock import MagicMock
    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"response": "{}"}

    # Mockamos a chamada http(s) da nova camada de provider, mas se estivermos
    # testando o Text2SQLAgent antigo, ele usa httpx.AsyncClient.post.
    # Vamos mockar no nível do provider LLM futuramente, mas hoje testamos o post.
    with patch("httpx.AsyncClient.post", return_value=fake_response) as mocked_post:
        # Se falhar ou estiver usando outro provider, precisamos adaptar.
        try:
            await agent._call_llm("teste controlado")
        except AttributeError:
            pytest.fail("Agent falhou por falta de variável (ex: settings.OLLAMA_BASE_URL)")

        assert mocked_post.called, "OLLAMA endpoint was not called"
        called_url = mocked_post.await_args.args[0]
        assert called_url == f"{settings.OLLAMA_HOST}/api/generate"

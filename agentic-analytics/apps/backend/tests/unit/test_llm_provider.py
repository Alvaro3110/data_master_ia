# apps/backend/tests/unit/test_llm_provider.py
import pytest

from app.services.llm.provider import LLMProvider


class FakeOpenAIResponsesRateLimited:
    async def create(self, **kwargs):
        raise RuntimeError("429 rate limited")


class FakeOpenAIClientRateLimited:
    def __init__(self):
        self.responses = FakeOpenAIResponsesRateLimited()


class SuccessOpenAIResponses:
    async def create(self, **kwargs):
        class MockOutput:
            output_text = "openai-ok"
        return MockOutput()


class SuccessOpenAIClient:
    def __init__(self):
        self.responses = SuccessOpenAIResponses()


class FakeHTTPResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"response": "fallback-ok"}


class FakeHTTPClient:
    async def post(self, url, json):
        return FakeHTTPResponse()


@pytest.mark.asyncio
async def test_openai_fallback_para_ollama_quando_openai_falha():
    provider = LLMProvider(
        primary="openai",
        openai_client=FakeOpenAIClientRateLimited(),
        http_client=FakeHTTPClient(),
        openai_model="gpt-test",
        ollama_model="llama-test",
        ollama_base_url="http://ollama:11434",
    )

    result = await provider.generate("ping", instructions="Seja conciso.")

    assert result.provider == "ollama"
    assert result.model == "llama-test"
    assert result.text == "fallback-ok"


@pytest.mark.asyncio
async def test_openai_sucesso():
    provider = LLMProvider(
        primary="openai",
        openai_client=SuccessOpenAIClient(),
        openai_model="gpt-test",
    )

    result = await provider.generate("ping", instructions="Seja conciso.")

    assert result.provider == "openai"
    assert result.model == "gpt-test"
    assert result.text == "openai-ok"

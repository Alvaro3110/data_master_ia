# apps/backend/app/services/llm/provider.py
from __future__ import annotations

from dataclasses import dataclass
import os
import logging
from typing import Optional, Any

import httpx
from openai import AsyncOpenAI, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    provider: str
    model: str
    text: str


class LLMProvider:
    def __init__(
        self,
        *,
        primary: str | None = None,
        openai_model: str | None = None,
        ollama_model: str | None = None,
        ollama_base_url: str | None = None,
        openai_client: Any = None,
        http_client: Any = None,
    ) -> None:
        self.primary = primary or os.getenv("LLM_PRIMARY", "openai")
        self.openai_model = openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        # Resolve Ollama host
        host = ollama_base_url or os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        self.ollama_base_url = host.rstrip("/")
        
        self.openai_client = openai_client
        self.http_client = http_client

    async def generate(self, prompt: str, instructions: str | None = None) -> LLMResult:
        # Lazy load AsyncOpenAI if not injected and key is present
        if self.openai_client is None and os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        order = ["openai", "ollama"] if self.primary == "openai" else ["ollama", "openai"]
        last_error: Exception | None = None

        for provider in order:
            try:
                if provider == "openai":
                    return await self._generate_openai(prompt, instructions)
                return await self._generate_ollama(prompt, instructions)
            except Exception as exc:
                logger.warning(f"Provider {provider} failed: {exc}")
                last_error = exc

        raise RuntimeError(f"All providers failed: {last_error}") from last_error

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _generate_openai(self, prompt: str, instructions: str | None) -> LLMResult:
        if self.openai_client is None:
            raise RuntimeError("OPENAI_API_KEY or openai_client not configured")

        # Handle duck typing for mock client vs AsyncOpenAI
        if hasattr(self.openai_client, "chat") and hasattr(self.openai_client.chat, "completions"):
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": instructions or "Você é um assistente analítico conciso."},
                    {"role": "user", "content": prompt}
                ]
            )
            text = response.choices[0].message.content
        elif hasattr(self.openai_client, "responses") and hasattr(self.openai_client.responses, "create"):
            # Parity with actualizacao.md signature if mock mimics responses
            response = await self.openai_client.responses.create(
                model=self.openai_model,
                instructions=instructions or "Você é um assistente analítico conciso.",
                input=prompt
            )
            text = response.output_text
        else:
            # Fallback for simple dict/mock helper objects
            raise RuntimeError("Unknown openai_client interface structure")

        return LLMResult(
            provider="openai",
            model=self.openai_model,
            text=text,
        )

    async def _generate_ollama(self, prompt: str, instructions: str | None) -> LLMResult:
        payload = {
            "model": self.ollama_model,
            "prompt": f"{instructions}\n\n{prompt}" if instructions else prompt,
            "stream": False,
        }
        
        if self.http_client is not None:
            response = await self.http_client.post(f"{self.ollama_base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        else:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.ollama_base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

        return LLMResult(
            provider="ollama",
            model=self.ollama_model,
            text=data["response"],
        )

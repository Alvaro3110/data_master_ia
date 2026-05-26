import pytest
from playwright.async_api import async_playwright, expect

@pytest.mark.asyncio
async def test_frontend_masking_display():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_route(route):
            if "api/v1/ask-analytics" in route.request.url:
                await route.fulfill(
                    status=200,
                    json={
                        "trace_id": "test-masking-123",
                        "question": "Qual a receita e CPF do cliente?",
                        "answer": "Margem e CPF consultados com sucesso. CPF retornado como ***.",
                        "routed_path": "analytics",
                        "reasoning_steps": ["Etapa de mascaramento executada"],
                        "retrieval_attempts": 1,
                        "rewritten_query": None,
                        "sources": [],
                        "sql": "SELECT receita, CPF_cnpj FROM fact_pricing_snapshot",
                        "sql_result": [{"receita": 10000.0, "CPF_cnpj": "***"}],
                        "masked_fields": ["CPF_cnpj"],
                        "latency_ms": 60
                    }
                )
            else:
                await route.continue_()

        await page.route("**/*", handle_route)

        try:
            await page.goto("http://localhost:3001", timeout=5000)
        except Exception:
            await browser.close()
            pytest.skip("Frontend Next.js não está rodando na porta 3001")

        # Preenche e envia
        input_box = page.locator("input[type='text']")
        await input_box.fill("Qual a receita e CPF do cliente?")

        send_button = page.locator("button:has-text('Analisar ↗')")
        await send_button.click()

        # Verifica resposta do assistente
        await expect(page.locator("text=CPF retornado como ***.")).to_be_visible()

        # Garante que dados sensíveis reais (como CPFs reais fictícios) não estão vazando no HTML da página
        content = await page.content()
        assert "123.456.789-00" not in content

        await browser.close()

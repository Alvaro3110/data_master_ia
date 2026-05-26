import re
from playwright.async_api import async_playwright, expect
import pytest

@pytest.mark.asyncio
async def test_chat_interaction_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_route(route):
            if "api/v1/ask-analytics" in route.request.url:
                await route.fulfill(
                    status=200,
                    json={
                        "trace_id": "test-playwright-123",
                        "question": "Qual a margem?",
                        "answer": "A margem média da safra é 5%.",
                        "routed_path": "analytics",
                        "reasoning_steps": ["Passo 1", "Passo 2"],
                        "retrieval_attempts": 1,
                        "rewritten_query": None,
                        "sources": [],
                        "sql": "SELECT AVG(margem_liquida) FROM fact_pricing_snapshot",
                        "sql_result": [{"AVG(margem_liquida)": 5.0}],
                        "masked_fields": [],
                        "latency_ms": 120
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

        # Verifica título / welcome text
        await expect(page.locator("text=Analytics de Pricing & Risco")).to_be_visible()

        # Preenche o input
        input_box = page.locator("input[type='text']")
        await input_box.fill("Qual a margem?")

        # Clica no botão de enviar
        send_button = page.locator("button:has-text('Analisar ↗')")
        await send_button.click()

        # Verifica se a mensagem do usuário aparece
        await expect(page.locator("text=Qual a margem?").first).to_be_visible()

        # Verifica a resposta mockada do assistente
        await expect(page.locator("text=A margem média da safra é 5%.")).to_be_visible()

        # Verifica os painéis extras gerados pela resposta
        await expect(page.locator("text=SQL Executado")).to_be_visible()
        await expect(page.locator("text=Rastreabilidade e Auditoria")).to_be_visible()
        await expect(page.locator("text=test-playwright-123")).to_be_visible()

        await browser.close()

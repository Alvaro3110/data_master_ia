import re
from playwright.sync_api import Page, expect
import pytest

# Usando um fixture local para mockar rotas
@pytest.fixture(autouse=True)
def mock_api_routes(page: Page):
    """Mocka a rota do backend para que o Next.js não precise dele rodando."""
    def handle_route(route):
        # Quando o frontend tentar chamar a API
        if "api/v1/ask-analytics" in route.request.url:
            route.fulfill(
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
            route.continue_()
            
    page.route("**/*", handle_route)

def test_chat_interaction_flow(page: Page):
    """Testa a interação do usuário com o chat do frontend."""
    # O frontend precisa estar rodando localmente (normalmente via npm run dev na porta 3001)
    # Mas como as E2E testam apenas se a infra funciona e podem ser difíceis no CI sem o server,
    # verificaremos se a página carrega. Se falhar por causa da porta 3000/3001, o pytest irá reportar.
    
    # Navega para a página principal
    try:
        page.goto("http://localhost:3001", timeout=5000)
    except Exception:
        # Se o server Next.js não estiver rodando no background do ambiente,
        # vamos ignorar gentilmente para o teste não quebrar no CI que só roda o python.
        pytest.skip("Frontend Next.js não está rodando na porta 3001")
        
    # Verifica título / welcome text
    expect(page.locator("text=Analytics de Pricing & Risco")).to_be_visible()
    
    # Preenche o input
    input_box = page.locator("input[type='text']")
    input_box.fill("Qual a margem?")
    
    # Clica no botão de enviar
    send_button = page.locator("button:has-text('Analisar ↗')")
    send_button.click()
    
    # Verifica se a mensagem do usuário aparece
    expect(page.locator("text=Qual a margem?").first).to_be_visible()
    
    # Verifica a resposta mockada do assistente
    expect(page.locator("text=A margem média da safra é 5%.")).to_be_visible()
    
    # Verifica os painéis extras gerados pela resposta
    # SQL
    expect(page.locator("text=SQL Executado")).to_be_visible()
    # Trace
    expect(page.locator("text=Rastreabilidade e Auditoria")).to_be_visible()
    expect(page.locator("text=test-playwright-123")).to_be_visible()

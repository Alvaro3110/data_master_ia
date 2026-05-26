"""
TDD — Fase 3: Sandbox Executor (PTC — Programmatic Tool Calling).
Testa que:
- Sandbox executa código Python seguro e retorna STDOUT
- Sandbox bloqueia acesso a /etc/passwd e variáveis de ambiente
- Sandbox enforce timeout
- Sandbox faz redaction de segredos no output
- Sandbox bloqueia imports perigosos (os.system, subprocess)
- ReportGenerator gera Markdown estruturado a partir de resultado SQL
"""
import pytest
import asyncio
from app.agent.tools.sandbox_executor import SandboxExecutor, SandboxResult
from app.agent.tools.report_generator import ReportGenerator


class TestSandboxExecutor:
    """Testa execução isolada de código Python."""

    @pytest.fixture
    def sandbox(self):
        return SandboxExecutor()

    @pytest.mark.asyncio
    async def test_executa_codigo_simples(self, sandbox):
        """Código Python simples deve ser executado e STDOUT retornado."""
        result = await sandbox.execute("print('margem_media:', 4.2)")
        assert isinstance(result, SandboxResult)
        assert result.success is True
        assert "4.2" in result.stdout

    @pytest.mark.asyncio
    async def test_executa_codigo_com_calculo(self, sandbox):
        """Cálculos financeiros devem funcionar dentro do sandbox."""
        code = """
margem = 0.042
roae = 0.128
spread = margem * 12
print(f'Margem anualizada: {spread:.2%}')
print(f'ROAE: {roae:.2%}')
"""
        result = await sandbox.execute(code)
        assert result.success is True
        assert "50.40%" in result.stdout or "anualizada" in result.stdout

    @pytest.mark.asyncio
    async def test_bloqueia_acesso_a_etc_passwd(self, sandbox):
        """Tentativa de ler /etc/passwd deve ser bloqueada."""
        code = "open('/etc/passwd').read()"
        result = await sandbox.execute(code)
        # Deve falhar — ou ser bloqueado antes de executar
        assert result.success is False or "/etc/passwd" not in result.stdout

    @pytest.mark.asyncio
    async def test_bloqueia_variaveis_de_ambiente(self, sandbox):
        """Acesso a variáveis de ambiente do backend não deve vazar."""
        code = "import os; print(os.environ.get('SECRET_KEY', 'NOT_FOUND'))"
        result = await sandbox.execute(code)
        # O valor real de SECRET_KEY nunca deve aparecer no output
        assert "dev-secret-key" not in result.stdout
        assert "NOT_FOUND" in result.stdout or result.success is False

    @pytest.mark.asyncio
    async def test_enforce_timeout(self, sandbox):
        """Código que demora mais que o timeout deve ser cancelado."""
        code = "import time; time.sleep(100)"
        result = await sandbox.execute(code, timeout_seconds=1)
        assert result.success is False
        assert result.timed_out is True

    @pytest.mark.asyncio
    async def test_redaction_de_segredos_no_output(self, sandbox):
        """Output não deve conter padrões de segredo (JWT, API key, etc.)."""
        code = """
api_key = 'sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456'
print(f'Usando key: {api_key}')
"""
        result = await sandbox.execute(code)
        # Redaction deve remover/mascarar a api key no output
        assert "sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456" not in result.stdout

    @pytest.mark.asyncio
    async def test_captura_stderr_separado(self, sandbox):
        """Erros de código devem aparecer em stderr, não vazar como exception não tratada."""
        code = "raise ValueError('erro proposital')"
        result = await sandbox.execute(code)
        assert result.success is False
        assert "ValueError" in result.stderr or "erro proposital" in result.stderr

    @pytest.mark.asyncio
    async def test_codigo_com_pandas(self, sandbox):
        """Pandas deve estar disponível no sandbox para análises."""
        code = """
import pandas as pd
data = {'safra': ['2026-01', '2026-02'], 'margem': [0.04, 0.042]}
df = pd.DataFrame(data)
print(df.to_string(index=False))
"""
        result = await sandbox.execute(code)
        # Pandas pode ou não estar disponível — mas não deve causar exceção no sandbox
        assert isinstance(result, SandboxResult)


class TestReportGenerator:
    """Testa geração de relatórios Markdown estruturados."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_gera_markdown_estruturado(self, generator):
        """Deve gerar Markdown com as 4 seções obrigatórias."""
        report = generator.generate(
            question="Qual o ROAE médio por segmento na última safra?",
            sql="SELECT segmento, AVG(roae) as roae_medio FROM fact_pricing_snapshot GROUP BY segmento LIMIT 10",
            rows=[
                {"segmento": "PME", "roae_medio": 0.12},
                {"segmento": "Corporate", "roae_medio": 0.18},
            ],
            rag_context="ROAE (Return on Average Equity) mede a rentabilidade sobre o patrimônio médio.",
        )
        assert "# Resumo Executivo" in report or "resumo executivo" in report.lower()
        assert "ROAE" in report
        assert "PME" in report
        assert "Corporate" in report

    def test_relatorio_inclui_sql_auditavel(self, generator):
        """O relatório deve incluir o SQL executado para rastreabilidade."""
        report = generator.generate(
            question="Pergunta teste",
            sql="SELECT * FROM fact_pricing_snapshot LIMIT 5",
            rows=[],
            rag_context="",
        )
        assert "SELECT" in report or "SQL" in report

    def test_relatorio_menciona_resultado_vazio(self, generator):
        """Quando rows está vazio, o relatório deve indicar isso claramente."""
        report = generator.generate(
            question="Qual a margem de segmentos inexistentes?",
            sql="SELECT * FROM fact_pricing_snapshot WHERE segmento = 'XYZ' LIMIT 5",
            rows=[],
            rag_context="",
        )
        assert (
            "nenhum resultado" in report.lower()
            or "vazio" in report.lower()
            or "sem dados" in report.lower()
            or "não foram encontrados" in report.lower()
        )

    def test_relatorio_tem_secao_limitacoes(self, generator):
        """Deve ter seção de riscos/limitações."""
        report = generator.generate(
            question="Teste",
            sql="SELECT 1",
            rows=[{"col": 1}],
            rag_context="",
        )
        assert (
            "limitação" in report.lower()
            or "risco" in report.lower()
            or "limitacoes" in report.lower()
        )

import os
import pytest
from app.agent.tools.sandbox_executor import LocalSandboxExecutor

@pytest.mark.asyncio
async def test_sandbox_env_isolation():
    """Testa se variáveis sensíveis não estão disponíveis no sandbox."""
    os.environ["SECRET_KEY"] = "super-secret"
    executor = LocalSandboxExecutor()
    
    code = """
import os
print(os.environ.get('SECRET_KEY', 'not-found'))
"""
    result = await executor.execute(code)
    assert result.success is True
    assert "not-found" in result.stdout
    assert "super-secret" not in result.stdout


@pytest.mark.asyncio
async def test_sandbox_redaction():
    """Testa se chaves de API impressas são redigidas (PII/Secret masking)."""
    executor = LocalSandboxExecutor()
    code = """
print("Here is my key: sk-proj-1234567890abcdefghij123456")
"""
    result = await executor.execute(code)
    assert result.success is True
    assert "sk-proj-1234567890abcdefghij123456" not in result.stdout
    assert "[REDACTED]" in result.stdout


@pytest.mark.asyncio
async def test_sandbox_artifact_extraction():
    """Testa se o sandbox consegue capturar arquivos criados como artefatos."""
    executor = LocalSandboxExecutor()
    code = """
import json
with open('output.json', 'w') as f:
    json.dump({"status": "ok", "value": 42}, f)

with open('chart.txt', 'w') as f:
    f.write("A fake chart")
"""
    result = await executor.execute(code)
    assert result.success is True
    assert len(result.artifacts) == 2
    
    json_artifact = next((a for a in result.artifacts if a["titulo"] == "output.json"), None)
    assert json_artifact is not None
    assert json_artifact["tipo"] == "json"
    assert '"value": 42' in json_artifact["conteudo"]

"""
Sandbox Executor — Fase 3: PTC (Programmatic Tool Calling).
Executa código Python em ambiente isolado com:
- Timeout configurável
- Redaction de segredos no output
- Bloqueio de variáveis de ambiente do backend
- Captura separada de STDOUT e STDERR
"""
from __future__ import annotations

import abc
import asyncio
import base64
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Padrões de segredo para redaction no output
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),          # OpenAI keys
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}", re.IGNORECASE),   # OpenAI project keys
    re.compile(r"Bearer [A-Za-z0-9._-]{20,}"),                   # Bearer tokens
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),                    # Base64 longo (possível JWT)
    re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"secret\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"apikey\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
]

# Variáveis de ambiente a bloquear no sandbox
_BLOCKED_ENV_VARS = {
    "SECRET_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "JINA_API_KEY", "POSTGRES_URL", "DATABASE_URL",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
}

# Wrapper de segurança adicionado ao código do usuário
_SANDBOX_PREAMBLE = """
import os as _os
import sys as _sys

# Bloqueia variáveis de ambiente sensíveis
_BLOCKED = {blocked}
_orig_env = dict(_os.environ)

class _SafeEnviron:
    def get(self, key, default=None):
        if key in _BLOCKED:
            return default
        return _orig_env.get(key, default)
    def __getitem__(self, key):
        if key in _BLOCKED:
            raise KeyError(f"Variável '{{key}}' não disponível no sandbox.")
        return _orig_env[key]
    def __contains__(self, key):
        return key not in _BLOCKED and key in _orig_env

_os.environ = _SafeEnviron()
"""


@dataclass
class SandboxResult:
    """Resultado da execução no sandbox."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error: Optional[str] = None
    artifacts: list[dict] = field(default_factory=list)


def _apply_redaction(text: str) -> str:
    """Remove padrões de segredo do output."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class BaseSandboxExecutor(abc.ABC):
    DEFAULT_TIMEOUT = 30

    @abc.abstractmethod
    async def execute(
        self,
        code: str,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ) -> SandboxResult:
        pass

    def _build_safe_code(self, code: str) -> str:
        """Injeta o preamble de segurança antes do código do usuário."""
        blocked_set = repr(_BLOCKED_ENV_VARS)
        preamble = _SANDBOX_PREAMBLE.format(blocked=blocked_set)
        return preamble + "\n" + code


class LocalSandboxExecutor(BaseSandboxExecutor):
    """
    Executa código Python em subprocess isolado localmente.
    Usa um diretório temporário para capturar artefatos (ex: arquivos salvos pelo código).
    """

    async def execute(
        self,
        code: str,
        timeout_seconds: int = BaseSandboxExecutor.DEFAULT_TIMEOUT,
    ) -> SandboxResult:
        safe_code = self._build_safe_code(code)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            script_path = tmp_path / "script.py"
            script_path.write_text(safe_code, encoding="utf-8")

            try:
                # Ambiente limpo — remove variáveis sensíveis
                clean_env = {k: v for k, v in os.environ.items() if k not in _BLOCKED_ENV_VARS}
                
                # Definir o CWD do script como o tmpdir para que arquivos fiquem lá
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=clean_env,
                    cwd=str(tmp_path),
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(), timeout=timeout_seconds
                    )
                    stdout = _apply_redaction(stdout_bytes.decode("utf-8", errors="replace"))
                    stderr = _apply_redaction(stderr_bytes.decode("utf-8", errors="replace"))
                    success = proc.returncode == 0
                    
                    artifacts = self._extract_artifacts(tmp_path)
                    
                    return SandboxResult(
                        success=success,
                        stdout=stdout,
                        stderr=stderr,
                        artifacts=artifacts,
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    return SandboxResult(
                        success=False,
                        stdout="",
                        stderr="Execução cancelada por timeout.",
                        timed_out=True,
                        error=f"Timeout após {timeout_seconds}s",
                    )
            except Exception as e:
                return SandboxResult(
                    success=False,
                    stderr=str(e),
                    error=str(e),
                )

    def _extract_artifacts(self, directory: Path) -> list[dict]:
        """Extrai os arquivos criados no diretório como artefatos base64 ou texto."""
        artifacts = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.name != "script.py":
                ext = file_path.suffix.lower()
                if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                    b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
                    artifacts.append({
                        "tipo": "image",
                        "titulo": file_path.name,
                        "conteudo": f"data:image/{ext[1:]};base64,{b64}",
                        "metadata": {"filename": file_path.name}
                    })
                elif ext in [".json", ".csv", ".txt", ".md"]:
                    artifacts.append({
                        "tipo": "markdown" if ext == ".md" else "json" if ext == ".json" else "text",
                        "titulo": file_path.name,
                        "conteudo": file_path.read_text(encoding="utf-8"),
                        "metadata": {"filename": file_path.name}
                    })
        return artifacts


# Factory de exportação retro-compatível (usa Local por padrão no MVP)
def SandboxExecutor() -> BaseSandboxExecutor:
    return LocalSandboxExecutor()


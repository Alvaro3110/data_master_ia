"""
Sandbox Executor — Fase 3: PTC (Programmatic Tool Calling).
Executa código Python em ambiente isolado com:
- Timeout configurável
- Redaction de segredos no output
- Bloqueio de variáveis de ambiente do backend
- Captura separada de STDOUT e STDERR
"""
from __future__ import annotations

import asyncio
import re
import subprocess
import sys
import tempfile
import os
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
    artifacts: list[str] = field(default_factory=list)


def _apply_redaction(text: str) -> str:
    """Remove padrões de segredo do output."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class SandboxExecutor:
    """
    Executa código Python em subprocess isolado.
    Aplica redaction de segredos e bloqueia variáveis de ambiente sensíveis.
    Impõe timeout configurável.
    """

    DEFAULT_TIMEOUT = 30

    def _build_safe_code(self, code: str) -> str:
        """Injeta o preamble de segurança antes do código do usuário."""
        blocked_set = repr(_BLOCKED_ENV_VARS)
        preamble = _SANDBOX_PREAMBLE.format(blocked=blocked_set)
        return preamble + "\n" + code

    async def execute(
        self,
        code: str,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ) -> SandboxResult:
        """
        Executa código Python em subprocess com timeout e redaction.

        Args:
            code: Código Python a executar.
            timeout_seconds: Limite de tempo em segundos.

        Returns:
            SandboxResult com stdout, stderr, success e timed_out.
        """
        safe_code = self._build_safe_code(code)

        # Cria arquivo temporário com o código
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(safe_code)
            tmp_path = f.name

        try:
            # Ambiente limpo — remove variáveis sensíveis do processo filho
            clean_env = {k: v for k, v in os.environ.items() if k not in _BLOCKED_ENV_VARS}

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=clean_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_seconds
                )
                stdout = _apply_redaction(stdout_bytes.decode("utf-8", errors="replace"))
                stderr = _apply_redaction(stderr_bytes.decode("utf-8", errors="replace"))
                success = proc.returncode == 0
                return SandboxResult(
                    success=success,
                    stdout=stdout,
                    stderr=stderr,
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
        finally:
            Path(tmp_path).unlink(missing_ok=True)

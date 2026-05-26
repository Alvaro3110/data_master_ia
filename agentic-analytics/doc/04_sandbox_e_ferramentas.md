# Sandbox e PTC (Programmatic Tool Calling)

O **Agentic Analytics** permite a elaboração de resultados complexos que vão muito além do mero texto. Para isso, na Fase 3, implementamos o conceito de Code Execution através de um **Sandbox Python Isolado**.

## 1. O SandboxExecutor (`app/agent/tools/sandbox_executor.py`)
Muitas vezes, a plataforma precisava processar um lote de informações tabulares resultantes de uma query SQL ou montar um gráfico de regressão para projetar cenários de margem. Para isso:
- O sistema permite que o Agente escreva scripts autônomos em Python usando `pandas` e `math`.
- Esses scripts rodam sob o `SandboxExecutor`, que levanta um subprocesso restrito (`subprocess.run`).

### Mecanismos de Segurança:
- **Environment Hiding:** As chaves de API, segredos da DB (DuckDB/PostgreSQL) e Tokens (como OPENAI_API_KEY) são completamente omitidos do ambiente que executa o subprocesso.
- **Redaction:** Toda a saída do script (`stdout` e `stderr`) passa por uma expressão regular e varredura heurística antes de ser exibida, impedindo vazamentos (*Data Leakage*).
- **Timeouts Rigorosos:** Um script infinito (`while True: pass`) é exterminado sumariamente, protegendo o backend contra travamentos propositais ou maliciosos.

## 2. ArtifactViewer e Relatórios de Markdown
Se o código sandbox produzir tabelas gigantes, ou se o agente produzir análises longas, exibir tudo de uma vez no chat estragaria a usabilidade.
- Adicionamos o pacote genérico de "Artefatos" no retorno da API.
- No React, desenvolvemos o componente `<ArtifactViewer />`, que isola essa saída complexa num bloco estilizado e rolável no frontend, mantendo o chat fluido.

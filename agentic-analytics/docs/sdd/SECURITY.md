# Objetivo
Consolidar políticas de segurança da aplicação para SQL, dados sensíveis, CORS e uso de segredos.

## Validador SQL
- O backend usa `sqlglot` com análise AST para validar SQL gerado por agentes.
- Bloqueios mínimos: DDL, DML, multi-statement, tabelas fora de whitelist e funções perigosas.
- Para tabelas grandes, exigir `LIMIT` para mitigar full scan sem governança.

## Mascaramento de PII
- Aplicar mascaramento em payloads antes de persistência de auditoria e resposta ao cliente.
- Garantir que campos sensíveis não apareçam em logs de aplicação.

## CORS
- Permitir apenas origens explícitas controladas.
- Não usar `allow_origins=["*"]` com credenciais ativas.

## Segredos e Custos LLM
- Chaves como `OPENAI_API_KEY` apenas em variáveis de ambiente.
- Testes de PR não podem depender de OpenAI real.
- Uso real deve ser controlado por marcação e ambiente apropriado.

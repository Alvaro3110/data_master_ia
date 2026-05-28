# Objetivo
Garantir rastreabilidade end-to-end de requisições, decisões dos agentes e eventos críticos.

## Trace ID
- Cada request recebe um `trace_id` no middleware.
- `trace_id` é retornado no header `X-Trace-ID` e no corpo JSON envelope.
- Eventos SSE devem incluir `trace_id` no evento de conclusão.

## Logs Estruturados
- Preferir logs estruturados para eventos críticos de segurança, SQL e latência.
- Registrar status de execução do fluxo agentic e nós percorridos.

## Métricas
- Monitorar latência e taxa de erro de endpoints críticos (`/health`, `/ask-analytics`).
- Acompanhar falhas de validação SQL e degradação de dependências externas.

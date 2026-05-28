# Objetivo
Registrar decisões em aberto que afetam contrato, rollout e governança para evitar implementação baseada em suposição.

## Questões em Aberto
- Q01: Qual versão de API (v1/v2) será adotada quando houver novo breaking change no envelope ou nos campos de `data`?
- Q02: Quando o gate de cobertura mínima (`pytest-cov`) entra como bloqueio obrigatório no CI principal?
- Q03: Qual stack oficial de observabilidade será priorizada para produção (OpenTelemetry, Langfuse ou híbrida)?
- Q04: Quais limites padrão de rate-limit por usuário e por workspace serão adotados no ambiente inicial?
- Q05: Qual política final para retenção de logs de auditoria e dados de trace (prazo e anonimização)?

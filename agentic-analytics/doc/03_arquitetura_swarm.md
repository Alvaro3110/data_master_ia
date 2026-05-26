# Arquitetura Swarm: O Coração do Agente

A inovação central do Agentic Analytics (na Fase 4) reside na implementação da Arquitetura Swarm usando `LangGraph`.

## Por que Swarm?
Um fluxo rígido de LangGraph comum opera como um DAG estreito (ex: Node A -> Node B -> Node C). Isso engessa a inteligência do sistema quando submetido a perguntas híbridas ou abertas. Ao migrarmos para o **Swarm**, empoderamos o orquestrador para funcionar como o *Manager* de uma equipe especializada.

## O Modelo de Atores
1. **Node `guardrail` (O Vigia):**
   - É o *entrypoint* do grafo. Inspeciona agressivamente cada requisição e barra (out_of_scope) aquilo que não pertence ao domínio financeiro do bot (prevenindo prompt injection e perdas de tempo com perguntas vazias).
2. **Node `supervisor` (O Orquestrador):**
   - Recebe a intenção limpa e a pergunta do vigia. Toma uma decisão de roteamento (Routing Decision).
   - Pode despachar a tarefa para o `data_agent`, para o `risk_agent`, ou se for muito complexa, para **ambos**.
3. **`data_agent` (O Cientista de Dados):**
   - Encarregado de ir a fundo nos dados numéricos brutos. Acessa esquemas de tabelas, constrói SQL via `text2sql_agent`, invoca e sumariza os dados usando Pandas no `sandbox_execute`.
4. **`risk_agent` (O Auditor):**
   - Acessa a base vetorial e BM25 (RAG). Seu objetivo é puxar as regras de *compliance* e avaliar o limite legal do que foi perguntado na política da empresa.

## TracePanel e a Transparência
Ao acoplar o **TracePanel** na interface React, transformamos a caixa-preta do LLM numa esteira visual de auditoria de dados:
- Todas as mensagens do tipo "Debate Swarm" são capturadas no estado do agente.
- O analista visualiza exatamente qual parte da pergunta foi resolvida pelo `data_agent` e qual ressalva foi levantada pelo `risk_agent` antes de confiar no resumo gerado na última etapa do grafo (`node_generate_answer`).

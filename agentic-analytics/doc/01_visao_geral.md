# Visão Geral: Agentic Analytics Platform

## O que é o projeto?
O **Agentic Analytics** é uma plataforma avançada de Inteligência Artificial focada no setor financeiro, desenhada para fornecer respostas rápidas, precisas e governadas sobre métricas de crédito, risco, margem e safras.

Diferente de chatbots tradicionais baseados apenas em geração de texto, a plataforma utiliza uma arquitetura **Multi-Agente (Swarm)**, orquestrando fluxos de pensamento complexos através de um **Supervisor** que delega tarefas para especialistas estritos, garantindo que regras de negócio, governança de dados e restrições de segurança sejam rigorosamente seguidas.

## Pilares Tecnológicos
1. **LangGraph & FastAPI (Backend):** Toda a esteira de raciocínio lógico é modelada como um grafo (estado de agentes) em LangGraph, empacotada em uma API RESTful de alta performance feita em FastAPI.
2. **Next.js & React (Frontend):** Painel interativo estilo ChatGPT, mas enriquecido com ferramentas analíticas (SQL Viewer, Visualizador de Artefatos em Markdown, TracePanel de auditoria do LLM).
3. **Persistência via SQLite:** Workspaces e Threads são armazenados e isolados para permitir uma continuidade conversacional.
4. **Execução de Código Segura (Sandbox):** O sistema consegue gerar, validar e executar códigos e análises em Python numa "sandbox", sem colocar o servidor principal em risco.

## O Desafio e a Solução
**Problema:** Analistas de risco precisavam de respostas que misturassem *conhecimento institucional (políticas em PDF/Markdown)* com *dados em tempo real (Data Warehouses)*, sem comprometer a exatidão. Uma alucinação de LLM poderia custar milhões.

**Solução:** Implementamos a arquitetura Swarm acoplada a TDD (Test-Driven Development) rigoroso. Em vez de um modelo único tentar resolver tudo, temos:
- **Guardrails** para bloquear perguntas fora de escopo.
- **RAG (Retrieval-Augmented Generation)** com busca híbrida para contexto de risco e políticas.
- **Text-to-SQL Governado** que traduz a semântica da pergunta para SQL executável, checando contra um AST (Abstract Syntax Tree) para impedir *SQL injection* e acessos a tabelas não autorizadas.

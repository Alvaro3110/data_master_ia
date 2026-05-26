"""
LangGraph Agentic Flow — 7 nós, padrão Week7 adaptado para pricing.
Fluxo: guardrail → route → [rag | text2sql | hybrid] → validate → execute → report → audit
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig

from app.agent.guardrail import GuardrailResult, classify_question
from app.config import settings


# ─── State ───────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """Estado do grafo — Swarm pattern."""
    question: str
    trace_id: str
    guardrail: GuardrailResult | None
    intent: Literal["conceptual", "analytics", "hybrid", "out_of_scope", "swarm"] | None
    rag_context: str | None          # chunks recuperados do OpenSearch
    rag_sources: list[str]           # fontes do RAG
    sql_plan: str | None             # SQL gerado pelo text2sql agent
    sql_result: list[dict] | None    # resultado da execução
    answer: str | None               # resposta final
    reasoning_steps: list[str]       # Week7: lista de passos de raciocínio
    retrieval_attempts: int          # Week7: contagem de tentativas
    rewritten_query: str | None      # Week7: query reescrita
    masked_fields: list[str]         # campos mascarados
    routed_path: str | None          # "rules_only" | "analytics" | "hybrid"
    sandbox_result: dict | None      # resultado da execução no sandbox (Fase 3)
    artifacts: list[dict]            # artefatos gerados (Fase 3)
    swarm_route: dict | None         # rota do orquestrador
    specialist_messages: list[dict]  # mensagens dos especialistas


class GraphConfig(TypedDict):
    """Configuração do grafo — Week7 pattern."""
    max_retrieval_attempts: int   # 2
    guardrail_threshold: int      # 60
    model: str                    # "llama3.2:1b"
    temperature: float            # 0.0
    top_k: int                    # 3


# ─── Nós do Grafo ─────────────────────────────────────────────────────────────

def node_guardrail(state: AgentState, config: RunnableConfig) -> dict:
    """
    Nó 1: Guardrail — valida escopo e classifica intenção.
    Week7 pattern: score 0-100, threshold=60.
    """
    cfg = config.get("configurable", {})
    threshold = cfg.get("guardrail_threshold", settings.GUARDRAIL_THRESHOLD)

    result = classify_question(state["question"])
    steps = list(state.get("reasoning_steps", []))
    steps.append(f"Validated query scope (score: {result.score}/100)")

    return {
        "guardrail": result,
        "intent": result.intent,
        "reasoning_steps": steps,
        "retrieval_attempts": 0,
        "rewritten_query": None,
        "rag_sources": [],
        "masked_fields": [],
        "sandbox_result": None,
        "artifacts": [],
        "swarm_route": None,
        "specialist_messages": [],
    }


def node_out_of_scope(state: AgentState) -> dict:
    """Nó 2: Resposta para perguntas fora de escopo."""
    steps = list(state.get("reasoning_steps", []))
    steps.append("Query rejected by guardrail — out of scope")
    return {
        "answer": (
            f"Esta pergunta está fora do domínio deste sistema analítico. "
            f"Motivo: {state['guardrail'].reason}. "
            "Este sistema responde perguntas sobre pricing, margem, safra, risco e ROAE."
        ),
        "reasoning_steps": steps,
        "routed_path": "rejected",
    }


def node_supervisor(state: AgentState, config: RunnableConfig) -> dict:
    """Nó 3: Supervisor do Swarm — decide quais especialistas chamar."""
    from app.agent.orchestrator import Orchestrator
    
    steps = list(state.get("reasoning_steps", []))
    orchestrator = Orchestrator()
    route = orchestrator.route(state["question"])
    
    steps.append(f"Supervisor routed to: {', '.join(route.required_agents)}")
    return {
        "swarm_route": {
            "target": route.target_agent,
            "required": route.required_agents,
        },
        "reasoning_steps": steps,
        "routed_path": "swarm_" + route.target_agent,
    }


async def node_data_agent(state: AgentState, config: RunnableConfig) -> dict:
    """Nó 4a: Data Agent — extrai números e SQL."""
    from app.agent.specialists.data_agent import DataAgent
    
    steps = list(state.get("reasoning_steps", []))
    agent = DataAgent()
    resp = await agent.process(state["question"])
    
    msgs = list(state.get("specialist_messages", []))
    msgs.append({"agent": "data_agent", "content": resp["content"]})
    steps.append("Data Agent processed query")
    
    return {
        "specialist_messages": msgs,
        "reasoning_steps": steps,
        "sql_plan": resp.get("sql"),
        "sql_result": resp.get("sql_result"),
        "masked_fields": resp.get("masked_fields", []),
        "rag_sources": resp.get("sources", []),
    }


async def node_risk_agent(state: AgentState, config: RunnableConfig) -> dict:
    """Nó 4b: Risk Agent — avalia políticas e riscos."""
    from app.agent.specialists.risk_agent import RiskAgent
    
    steps = list(state.get("reasoning_steps", []))
    agent = RiskAgent()
    resp = await agent.process(state["question"])
    
    msgs = list(state.get("specialist_messages", []))
    msgs.append({"agent": "risk_agent", "content": resp["content"]})
    steps.append("Risk Agent processed query")
    
    # Adiciona fontes de risco se existirem
    sources = list(state.get("rag_sources", []))
    for s in resp.get("sources", []):
        if s not in sources:
            sources.append(s)
            
    return {
        "specialist_messages": msgs,
        "reasoning_steps": steps,
        "rag_sources": sources,
    }


def node_rewrite_query(state: AgentState, config: RunnableConfig) -> dict:
    """Nó 5: Reescrita de query — Week7 pattern."""
    from app.agent.query_rewriter import rewrite_query

    steps = list(state.get("reasoning_steps", []))
    original = state["question"]
    rewritten = rewrite_query(
        question=original,
        guardrail_result=state.get("guardrail"),
        retrieval_feedback=state.get("rag_context", ""),
    )
    steps.append(f"Rewritten query for better results")
    return {
        "rewritten_query": rewritten,
        "reasoning_steps": steps,
    }


async def node_sandbox_execute(state: AgentState, config: RunnableConfig) -> dict:
    """Nó 5.5: Execução no Sandbox (PTC)."""
    from app.agent.tools.sandbox_executor import SandboxExecutor
    
    steps = list(state.get("reasoning_steps", []))
    # Para o MVP da Fase 3, se houver instrução explícita de código no state, executamos
    # Caso contrário, apenas passamos reto. No futuro, isso será ativado via function calling do LLM.
    code_to_run = config.get("configurable", {}).get("sandbox_code")
    
    if code_to_run:
        executor = SandboxExecutor()
        result = await executor.execute(code_to_run)
        steps.append(f"Executed Python code in Sandbox (Success: {result.success})")
        return {
            "sandbox_result": {
                "success": result.success,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            "reasoning_steps": steps,
        }
    return {}


def node_generate_answer(state: AgentState, config: RunnableConfig) -> dict:
    """Nó 6: Sintetização do Swarm."""
    from app.agent.orchestrator import Orchestrator, SwarmMessage
    
    steps = list(state.get("reasoning_steps", []))
    orchestrator = Orchestrator()
    
    msgs = [
        SwarmMessage(agent=m["agent"], content=m["content"]) 
        for m in state.get("specialist_messages", [])
    ]
    
    answer = orchestrator.synthesize(state["question"], msgs)
    steps.append("Orchestrator synthesized final answer")
    
    # Mantendo retrocompatibilidade de artifacts (Fase 3)
    artifacts = list(state.get("artifacts", []))
    if state.get("sql_result") is not None:
        from app.agent.tools.report_generator import ReportGenerator
        generator = ReportGenerator()
        report_md = generator.generate(
            question=state["question"],
            sql=state.get("sql_plan", ""),
            rows=state.get("sql_result", []),
            rag_context=state.get("rag_context", ""),
            trace_id=state.get("trace_id"),
            masked_fields=state.get("masked_fields", []),
        )
        artifacts.append({
            "tipo": "markdown",
            "conteudo": report_md,
            "titulo": "Relatório Analítico",
        })

    return {
        "answer": answer,
        "reasoning_steps": steps,
        "artifacts": artifacts,
    }


# ─── Edges (condicionais) ──────────────────────────────────────────────────────

def edge_after_guardrail(state: AgentState, config: RunnableConfig) -> str:
    """Decide próximo nó após o guardrail."""
    guardrail = state.get("guardrail")
    cfg = config.get("configurable", {})
    threshold = cfg.get("guardrail_threshold", settings.GUARDRAIL_THRESHOLD)

    if not guardrail or not guardrail.allowed or guardrail.score < threshold:
        return "out_of_scope"

    return "supervisor"


def edge_after_supervisor(state: AgentState, config: RunnableConfig) -> list[str]:
    """Após supervisor: dispara agentes especialistas em paralelo."""
    route = state.get("swarm_route", {})
    required = route.get("required", [])
    
    if "data_agent" in required and "risk_agent" in required:
        return ["data_agent", "risk_agent"]
    elif "data_agent" in required:
        return ["data_agent"]
    elif "risk_agent" in required:
        return ["risk_agent"]
    
    return ["generate_answer"]


def edge_after_specialist(state: AgentState, config: RunnableConfig) -> str:
    """Após especialista: vai para sandbox ou sintetização."""
    return "generate_answer"


# ─── Build Graph ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Constrói e compila o grafo LangGraph de 7 nós."""
    graph = StateGraph(AgentState)

    # Adiciona nós
    graph.add_node("guardrail", node_guardrail)
    graph.add_node("out_of_scope", node_out_of_scope)
    graph.add_node("supervisor", node_supervisor)
    graph.add_node("data_agent", node_data_agent)
    graph.add_node("risk_agent", node_risk_agent)
    graph.add_node("rewrite_query", node_rewrite_query)
    graph.add_node("sandbox_execute", node_sandbox_execute)
    graph.add_node("generate_answer", node_generate_answer)

    # Entry point
    graph.set_entry_point("guardrail")

    # Edges condicionais
    graph.add_conditional_edges("guardrail", edge_after_guardrail, {
        "out_of_scope": "out_of_scope",
        "supervisor": "supervisor",
    })
    
    # Roteamento do Supervisor para os agentes (pode ser paralelo)
    graph.add_conditional_edges(
        "supervisor",
        edge_after_supervisor,
        ["data_agent", "risk_agent", "generate_answer"]
    )
    
    # Retorno dos agentes (simplificado para ir direto pra sandbox/sintetizar no MVP)
    graph.add_conditional_edges("data_agent", edge_after_specialist, {
        "sandbox_execute": "sandbox_execute",
        "generate_answer": "generate_answer",
    })
    graph.add_conditional_edges("risk_agent", edge_after_specialist, {
        "sandbox_execute": "sandbox_execute",
        "generate_answer": "generate_answer",
    })

    # Edges fixos
    graph.add_edge("sandbox_execute", "generate_answer")
    graph.add_edge("out_of_scope", END)
    graph.add_edge("generate_answer", END)

    return graph.compile()


# Instância singleton
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_analytics(
    question: str,
    trace_id: str | None = None,
    config: dict | None = None,
) -> dict:
    """
    Ponto de entrada público — executa o fluxo agentic completo.

    Returns:
        dict com: answer, trace_id, routed_path, reasoning_steps,
                  retrieval_attempts, rewritten_query, sources, sql, masked_fields
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    graph_config = {
        "configurable": {
            "max_retrieval_attempts": settings.MAX_RETRIEVAL_ATTEMPTS,
            "guardrail_threshold": settings.GUARDRAIL_THRESHOLD,
            "model": settings.OLLAMA_MODEL,
            "temperature": 0.0,
            "top_k": 3,
            **(config or {}),
        }
    }

    initial_state: AgentState = {
        "question": question,
        "trace_id": trace_id,
        "guardrail": None,
        "intent": None,
        "rag_context": None,
        "rag_sources": [],
        "sql_plan": None,
        "sql_result": None,
        "answer": None,
        "reasoning_steps": [],
        "retrieval_attempts": 0,
        "rewritten_query": None,
        "masked_fields": [],
        "routed_path": None,
        "sandbox_result": None,
        "artifacts": [],
        "swarm_route": None,
        "specialist_messages": [],
    }

    graph = get_graph()
    final_state = await graph.ainvoke(initial_state, config=graph_config)

    return {
        "trace_id": trace_id,
        "question": question,
        "answer": final_state.get("answer", "Não foi possível gerar uma resposta."),
        "routed_path": final_state.get("routed_path", "unknown"),
        "reasoning_steps": final_state.get("reasoning_steps", []),
        "retrieval_attempts": final_state.get("retrieval_attempts", 0),
        "rewritten_query": final_state.get("rewritten_query"),
        "sources": final_state.get("rag_sources", []),
        "sql": final_state.get("sql_plan"),
        "sql_result": final_state.get("sql_result"),
        "masked_fields": final_state.get("masked_fields", []),
        "sandbox_result": final_state.get("sandbox_result"),
        "artifacts": final_state.get("artifacts", []),
        "specialist_messages": final_state.get("specialist_messages", []),
    }


async def run_analytics_stream(
    question: str,
    trace_id: str,
    config: dict | None = None,
) -> None:
    """Runs the graph, streaming steps and answer chunks to Redis."""
    import asyncio
    from app.services.redis_client import redis_mgr

    graph_config = {
        "configurable": {
            "max_retrieval_attempts": settings.MAX_RETRIEVAL_ATTEMPTS,
            "guardrail_threshold": settings.GUARDRAIL_THRESHOLD,
            "model": settings.OLLAMA_MODEL,
            "temperature": 0.0,
            "top_k": 3,
            **(config or {}),
        }
    }

    initial_state: AgentState = {
        "question": question,
        "trace_id": trace_id,
        "guardrail": None,
        "intent": None,
        "rag_context": None,
        "rag_sources": [],
        "sql_plan": None,
        "sql_result": None,
        "answer": None,
        "reasoning_steps": [],
        "retrieval_attempts": 0,
        "rewritten_query": None,
        "masked_fields": [],
        "routed_path": None,
        "sandbox_result": None,
        "artifacts": [],
        "swarm_route": None,
        "specialist_messages": [],
    }

    graph = get_graph()

    await redis_mgr.add_event(trace_id, "start", {"question": question})

    final_state = initial_state.copy()

    try:
        async for event in graph.astream(initial_state, config=graph_config):
            for node_name, output in event.items():
                for key, val in output.items():
                    if isinstance(val, list) and key in final_state and isinstance(final_state[key], list):
                        merged = list(final_state[key])
                        for item in val:
                            if item not in merged:
                                merged.append(item)
                        final_state[key] = merged
                    else:
                        final_state[key] = val

                steps = output.get("reasoning_steps", [])
                new_step = steps[-1] if steps else f"Executed {node_name}"

                await redis_mgr.add_event(trace_id, "step", {
                    "node": node_name,
                    "reasoning_step": new_step,
                    "sql": output.get("sql_plan") or final_state.get("sql_plan"),
                    "sql_result": output.get("sql_result") or final_state.get("sql_result"),
                    "routed_path": output.get("routed_path") or final_state.get("routed_path"),
                })

        answer = final_state.get("answer") or "Não foi possível gerar uma resposta."

        # Simular streaming chunk-by-chunk para resposta final do assistente
        words = answer.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            await redis_mgr.add_event(trace_id, "chunk", {"text": chunk})
            await asyncio.sleep(0.015)

        # Emitir evento final contendo resposta completa
        final_payload = {
            "trace_id": trace_id,
            "question": question,
            "answer": answer,
            "routed_path": final_state.get("routed_path", "unknown"),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            "retrieval_attempts": final_state.get("retrieval_attempts", 0),
            "rewritten_query": final_state.get("rewritten_query"),
            "sources": final_state.get("rag_sources", []),
            "sql": final_state.get("sql_plan"),
            "sql_result": final_state.get("sql_result"),
            "masked_fields": final_state.get("masked_fields", []),
            "artifacts": final_state.get("artifacts", []),
            "sandbox_result": final_state.get("sandbox_result"),
            "specialist_messages": final_state.get("specialist_messages", []),
            "status": "success",
        }
        await redis_mgr.add_event(trace_id, "done", final_payload)

    except Exception as e:
        await redis_mgr.add_event(trace_id, "error", {"detail": str(e)})
        raise e


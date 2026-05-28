"use client";
import { useState, useRef, useCallback, useEffect, KeyboardEvent } from "react";
import { SQLViewer } from "./SQLViewer";
import { SourcesPanel } from "./SourcesPanel";
import { TracePanel } from "./TracePanel";
import { ArtifactViewer } from "./ArtifactViewer";

const EXAMPLE_QUESTIONS = [
  "O que significa safra nesta base?",
  "Qual foi a margem média por safra no segmento PME?",
  "Quais produtos tiveram pior ROAE na última safra?",
  "Explique a regra de alto risco e compare inadimplência por safra",
];

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  trace?: any;
  sql?: string | null;
  sqlResult?: any[] | null;
  sources?: string[];
  maskedFields?: string[];
  artifacts?: any[];
  sandboxResult?: any;
  specialistMessages?: any[];
  routedPath?: string;
  latencyMs?: number;
}

interface ChatPanelProps {
  apiUrl: string;
  workspaceId?: string;  // Fase 2: workspace opcional
}

function unwrapData<T>(payload: unknown): T {
  if (
    payload &&
    typeof payload === "object" &&
    "data" in payload
  ) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

export function ChatPanel({ apiUrl, workspaceId }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Limpa conexões pendentes no unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Carrega threads e histórico quando muda o workspace
  useEffect(() => {
    if (!workspaceId) {
      setActiveThreadId(null);
      setMessages([]);
      return;
    }

    const loadWorkspaceThread = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/v1/workspaces/${workspaceId}/threads`);
        if (!res.ok) throw new Error("Erro ao carregar threads");
        const threads = unwrapData<any[]>(await res.json());

        let threadId = "";
        let historicalMessages: Message[] = [];

        if (threads.length > 0) {
          const thread = threads[0];
          threadId = thread.id;
          historicalMessages = (thread.mensagens || []).map((m: any, idx: number) => {
            const meta = m.metadata || {};
            return {
              id: `${threadId}-msg-${idx}`,
              role: m.role,
              content: m.content,
              trace: {
                trace_id: meta.trace_id,
                reasoning_steps: meta.specialist_messages ? [] : [],
                routed_path: meta.routed_path || "unknown",
              },
              sql: meta.sql || null,
              sqlResult: meta.sql_result || null,
              sources: meta.sources || [],
              maskedFields: meta.masked_fields || [],
              artifacts: meta.artifacts || [],
              sandboxResult: meta.sandbox_result || null,
              specialistMessages: meta.specialist_messages || [],
              routedPath: meta.routed_path || null,
            };
          });
        } else {
          // Cria uma thread nova padrão caso não exista
          const createRes = await fetch(`${apiUrl}/api/v1/workspaces/${workspaceId}/threads`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ titulo: "Análise Principal" }),
          });
          if (createRes.ok) {
            const newThread = unwrapData<any>(await createRes.json());
            threadId = newThread.id;
          }
        }

        setActiveThreadId(threadId);
        setMessages(historicalMessages);
        setTimeout(scrollToBottom, 100);
      } catch (err) {
        console.error("Falha ao carregar contexto de thread:", err);
      }
    };

    loadWorkspaceThread();
  }, [workspaceId, apiUrl]);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || loading) return;
      setError(null);

      const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content: question,
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);

      let traceId = "";
      try {
        const initRes = await fetch(`${apiUrl}/api/v1/ask-analytics/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            ...(workspaceId ? { workspace_id: workspaceId } : {}),
            ...(activeThreadId ? { thread_id: activeThreadId } : {}),
          }),
        });

        if (!initRes.ok) throw new Error(`HTTP ${initRes.status}`);
        const initData = unwrapData<{ trace_id: string }>(await initRes.json());
        traceId = initData.trace_id;
      } catch (e: any) {
        setError(`Erro ao iniciar análise: ${e.message}`);
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `⚠️ Falha ao conectar com o serviço analítico: ${e.message}`,
        };
        setMessages((prev) => [...prev, errorMsg]);
        setLoading(false);
        return;
      }

      const assistantMsgId = traceId || (Date.now() + 1).toString();
      const initialAssistantMsg: Message = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        trace: {
          reasoning_steps: [],
        },
      };
      setMessages((prev) => [...prev, initialAssistantMsg]);
      setTimeout(scrollToBottom, 100);

      let lastEventId = "0-0";
      let reconnectAttempts = 0;
      const maxReconnectAttempts = 5;

      const connectSSE = () => {
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        const sseUrl = `${apiUrl}/api/v1/ask-analytics/stream/${traceId}?last_event_id=${lastEventId}`;
        const es = new EventSource(sseUrl);
        eventSourceRef.current = es;

        es.addEventListener("start", () => {
          reconnectAttempts = 0;
        });

        es.addEventListener("step", (e: any) => {
          lastEventId = e.lastEventId || e.id || lastEventId;
          try {
            const data = JSON.parse(e.data);
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantMsgId) return m;
                const currentSteps = m.trace?.reasoning_steps || [];
                const nextSteps = [...currentSteps];
                if (data.reasoning_step && !nextSteps.includes(data.reasoning_step)) {
                  nextSteps.push(data.reasoning_step);
                }
                return {
                  ...m,
                  sql: data.sql || m.sql,
                  sqlResult: data.sql_result || m.sqlResult,
                  routedPath: data.routed_path || m.routedPath,
                  trace: {
                    ...m.trace,
                    reasoning_steps: nextSteps,
                    routed_path: data.routed_path || m.trace?.routed_path || "unknown",
                  },
                };
              })
            );
            setTimeout(scrollToBottom, 50);
          } catch (err) {
            console.error("Falha ao ler step:", err);
          }
        });

        es.addEventListener("chunk", (e: any) => {
          lastEventId = e.lastEventId || e.id || lastEventId;
          try {
            const data = JSON.parse(e.data);
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantMsgId) return m;
                return {
                  ...m,
                  content: m.content + data.text,
                };
              })
            );
            setTimeout(scrollToBottom, 50);
          } catch (err) {
            console.error("Falha ao ler chunk:", err);
          }
        });

        es.addEventListener("done", (e: any) => {
          lastEventId = e.lastEventId || e.id || lastEventId;
          try {
            const data = JSON.parse(e.data);
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantMsgId) return m;
                return {
                  ...m,
                  content: data.answer,
                  trace: {
                    trace_id: data.trace_id,
                    reasoning_steps: data.reasoning_steps || m.trace?.reasoning_steps || [],
                    retrieval_attempts: data.retrieval_attempts || 0,
                    rewritten_query: data.rewritten_query || null,
                    routed_path: data.routed_path || "unknown",
                    latency_ms: data.latency_ms || 0,
                  },
                  sql: data.sql,
                  sqlResult: data.sql_result,
                  sources: data.sources || [],
                  maskedFields: data.masked_fields || [],
                  artifacts: data.artifacts || [],
                  sandboxResult: data.sandbox_result,
                  specialistMessages: data.specialist_messages || [],
                  routedPath: data.routed_path,
                  latencyMs: data.latency_ms,
                };
              })
            );
            es.close();
            setLoading(false);
            setTimeout(scrollToBottom, 100);
          } catch (err) {
            console.error("Falha ao ler done:", err);
            es.close();
            setLoading(false);
          }
        });

        es.addEventListener("error", () => {
          es.close();
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const timeoutMs = Math.pow(2, reconnectAttempts) * 500;
            console.warn(`SSE desconectado. Tentando reconectar em ${timeoutMs}ms...`);
            setTimeout(connectSSE, timeoutMs);
          } else {
            setError("Erro na conexão streaming: limite de reconexões atingido.");
            setLoading(false);
          }
        });
      };

      connectSSE();
    },
    [apiUrl, loading, workspaceId, activeThreadId]
  );

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleExampleClick = (q: string) => {
    setInput(q);
    sendMessage(q);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        gap: "1rem",
      }}
    >
      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "1.5rem",
          padding: "0.5rem",
        }}
      >
        {/* Welcome state */}
        {messages.length === 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "1.5rem",
              padding: "3rem 1rem",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "3.5rem" }}>🧠</div>
            <div>
              <h2
                style={{
                  color: "#f1f5f9",
                  fontSize: "1.4rem",
                  fontWeight: 700,
                  marginBottom: "0.5rem",
                }}
              >
                Analytics de Pricing & Risco
              </h2>
              <p style={{ color: "#64748b", fontSize: "0.9rem" }}>
                Pergunte sobre margem, safra, ROAE, risco e muito mais.
              </p>
            </div>

            {/* Example prompts */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "0.75rem",
                width: "100%",
                maxWidth: "36rem",
              }}
            >
              {EXAMPLE_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleClick(q)}
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "0.75rem",
                    padding: "0.75rem",
                    color: "#94a3b8",
                    fontSize: "0.78rem",
                    cursor: "pointer",
                    textAlign: "left",
                    lineHeight: 1.4,
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLElement).style.background = "rgba(124,58,237,0.1)";
                    (e.target as HTMLElement).style.borderColor = "#7c3aed";
                    (e.target as HTMLElement).style.color = "#c4b5fd";
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                    (e.target as HTMLElement).style.borderColor = "rgba(255,255,255,0.1)";
                    (e.target as HTMLElement).style.color = "#94a3b8";
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg) => (
          <div key={msg.id} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {/* Bubble */}
            <div
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={{
                  maxWidth: "80%",
                  padding: "0.75rem 1rem",
                  borderRadius: msg.role === "user" ? "1rem 1rem 0.25rem 1rem" : "1rem 1rem 1rem 0.25rem",
                  background:
                    msg.role === "user"
                      ? "linear-gradient(135deg, #7c3aed, #6d28d9)"
                      : "rgba(255,255,255,0.05)",
                  border: msg.role === "user" ? "none" : "1px solid rgba(255,255,255,0.08)",
                  color: msg.role === "user" ? "#fff" : "#e2e8f0",
                  fontSize: "0.9rem",
                  lineHeight: 1.6,
                  boxShadow: msg.role === "user" ? "0 4px 16px rgba(124,58,237,0.3)" : "none",
                }}
              >
                {msg.content || (loading && msg.role === "assistant" ? "Carregando..." : "")}
              </div>
            </div>

            {/* Panels para resposta do assistente */}
            {msg.role === "assistant" && (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.75rem",
                  paddingLeft: "0.5rem",
                }}
              >
                {msg.sql && <SQLViewer sql={msg.sql} />}
                {msg.sources && msg.sources.length > 0 && (
                  <SourcesPanel sources={msg.sources} />
                )}
                {msg.artifacts && msg.artifacts.length > 0 && (
                  <ArtifactViewer artifacts={msg.artifacts} />
                )}
                {msg.trace && <TracePanel trace={msg.trace} specialistMessages={msg.specialistMessages} />}
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {loading && messages[messages.length - 1]?.role !== "assistant" && (
          <div
            data-testid="loading-indicator"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding: "0.75rem 1rem",
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "1rem 1rem 1rem 0.25rem",
              maxWidth: "12rem",
              color: "#64748b",
              fontSize: "0.85rem",
            }}
          >
            <div
              style={{
                display: "flex",
                gap: "0.3rem",
              }}
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    width: "6px",
                    height: "6px",
                    background: "#7c3aed",
                    borderRadius: "50%",
                    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                  }}
                />
              ))}
            </div>
            Analisando...
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            style={{
              padding: "0.75rem 1rem",
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "0.75rem",
              color: "#fca5a5",
              fontSize: "0.85rem",
            }}
          >
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          padding: "1rem",
          background: "rgba(255,255,255,0.03)",
          borderRadius: "1rem",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 -4px 24px rgba(0,0,0,0.2)",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Pergunte sobre pricing, margem, safra, risco ou ROAE..."
          disabled={loading}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#f1f5f9",
            fontSize: "0.9rem",
          }}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || loading}
          aria-label="Enviar pergunta"
          style={{
            background:
              input.trim() && !loading
                ? "linear-gradient(135deg, #7c3aed, #6d28d9)"
                : "rgba(255,255,255,0.05)",
            color: input.trim() && !loading ? "#fff" : "#475569",
            border: "none",
            borderRadius: "0.75rem",
            padding: "0.6rem 1.25rem",
            fontSize: "0.85rem",
            fontWeight: 600,
            cursor: input.trim() && !loading ? "pointer" : "not-allowed",
            transition: "all 0.2s ease",
            whiteSpace: "nowrap",
            boxShadow:
              input.trim() && !loading
                ? "0 4px 16px rgba(124,58,237,0.4)"
                : "none",
          }}
        >
          {loading ? "..." : "Analisar ↗"}
        </button>
      </div>
    </div>
  );
}

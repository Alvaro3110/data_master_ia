"use client";

interface TraceData {
  trace_id: string;
  reasoning_steps: string[];
  retrieval_attempts: number;
  rewritten_query: string | null;
  routed_path: string;
  latency_ms: number;
}

interface TracePanelProps {
  trace: TraceData | null;
  specialistMessages?: { agent: string; content: string }[];
}

function extractGuardrailScore(steps: string[]): string | null {
  for (const step of steps) {
    const match = step.match(/score:\s*(\d+\/\d+)/i);
    if (match) return match[1];
  }
  return null;
}

function getRouteColor(path: string): string {
  const colors: Record<string, string> = {
    hybrid: "#f59e0b",
    analytics: "#3b82f6",
    rules_only: "#10b981",
    rejected: "#ef4444",
    unknown: "#6b7280",
  };
  return colors[path] || "#6b7280";
}

function getStepIcon(step: string, idx: number): string {
  if (step.toLowerCase().includes("guardrail") || step.toLowerCase().includes("validated")) return "🛡️";
  if (step.toLowerCase().includes("rag") || step.toLowerCase().includes("retrieved")) return "🔍";
  if (step.toLowerCase().includes("sql") || step.toLowerCase().includes("generated")) return "🗄️";
  if (step.toLowerCase().includes("rewritten")) return "✏️";
  if (step.toLowerCase().includes("answer") || step.toLowerCase().includes("generated answer")) return "💬";
  return `${idx + 1}.`;
}

export function TracePanel({ trace, specialistMessages = [] }: TracePanelProps) {
  if (!trace) return null;

  const guardrailScore = extractGuardrailScore(trace.reasoning_steps);
  const routeColor = getRouteColor(trace.routed_path);

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1c1d30 100%)",
        borderRadius: "1rem",
        border: "1px solid #1e293b",
        overflow: "hidden",
        boxShadow: "0 4px 24px rgba(0, 0, 0, 0.3)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          background: "rgba(255, 255, 255, 0.03)",
          borderBottom: "1px solid #1e293b",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>🔍</span>
          <span
            style={{
              color: "#94a3b8",
              fontWeight: 600,
              fontSize: "0.8rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            Rastreabilidade
          </span>
        </div>
        {/* Latency badge */}
        <span
          style={{
            background: "#1e293b",
            color: "#64748b",
            borderRadius: "0.5rem",
            padding: "0.2rem 0.6rem",
            fontSize: "0.7rem",
            fontWeight: 600,
            fontFamily: "monospace",
          }}
        >
          ⏱ {trace.latency_ms}ms
        </span>
      </div>

      <div style={{ padding: "0.75rem 1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {/* Trace ID */}
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ color: "#475569", fontSize: "0.72rem" }}>trace_id</span>
          <code
            style={{
              color: "#94a3b8",
              fontSize: "0.72rem",
              background: "#0f172a",
              padding: "0.1rem 0.4rem",
              borderRadius: "0.25rem",
              border: "1px solid #1e293b",
              fontFamily: "monospace",
            }}
          >
            {trace.trace_id}
          </code>
        </div>

        {/* Route + Score */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <span
            style={{
              background: `${routeColor}20`,
              color: routeColor,
              border: `1px solid ${routeColor}`,
              borderRadius: "9999px",
              padding: "0.15rem 0.6rem",
              fontSize: "0.72rem",
              fontWeight: 700,
            }}
          >
            {trace.routed_path}
          </span>
          {guardrailScore && (
            <span
              style={{
                background: "rgba(124, 58, 237, 0.15)",
                color: "#a78bfa",
                border: "1px solid #7c3aed",
                borderRadius: "9999px",
                padding: "0.15rem 0.6rem",
                fontSize: "0.72rem",
                fontWeight: 700,
              }}
            >
              🛡️ {guardrailScore}
            </span>
          )}
        </div>

        {/* Reasoning Steps */}
        <div>
          <div
            style={{
              color: "#475569",
              fontSize: "0.7rem",
              marginBottom: "0.4rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Passos de raciocínio
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
            {trace.reasoning_steps.map((step, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  gap: "0.5rem",
                  alignItems: "flex-start",
                  padding: "0.4rem 0.6rem",
                  background: "rgba(255,255,255,0.02)",
                  borderRadius: "0.4rem",
                  border: "1px solid #1e293b",
                }}
              >
                <span style={{ fontSize: "0.85rem", flexShrink: 0 }}>
                  {getStepIcon(step, idx)}
                </span>
                <span style={{ color: "#94a3b8", fontSize: "0.75rem", lineHeight: 1.4 }}>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Swarm Specialist Messages */}
        {specialistMessages.length > 0 && (
          <div style={{ marginTop: "0.5rem" }}>
            <div
              style={{
                color: "#10b981",
                fontSize: "0.7rem",
                marginBottom: "0.4rem",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Debate Swarm
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              {specialistMessages.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: "rgba(16, 185, 129, 0.05)",
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                    borderRadius: "0.4rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.2rem",
                  }}
                >
                  <span
                    style={{
                      color: "#10b981",
                      fontSize: "0.65rem",
                      fontWeight: 700,
                      textTransform: "uppercase",
                    }}
                  >
                    🤖 {msg.agent.replace("_", " ")}
                  </span>
                  <span style={{ color: "#e2e8f0", fontSize: "0.75rem", lineHeight: 1.4 }}>
                    {msg.content}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rewritten query (se houver) */}
        {trace.rewritten_query && (
          <div
            style={{
              background: "rgba(245, 158, 11, 0.05)",
              border: "1px solid rgba(245, 158, 11, 0.2)",
              borderRadius: "0.5rem",
              padding: "0.6rem",
            }}
          >
            <div style={{ color: "#f59e0b", fontSize: "0.7rem", marginBottom: "0.25rem" }}>
              ✏️ Query reescrita
            </div>
            <div style={{ color: "#fde68a", fontSize: "0.78rem", fontStyle: "italic" }}>
              "{trace.rewritten_query}"
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

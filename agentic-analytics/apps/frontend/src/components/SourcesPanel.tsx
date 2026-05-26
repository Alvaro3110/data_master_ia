"use client";

interface SourcesPanelProps {
  sources: string[] | undefined;
}

function getSourceIcon(source: string): string {
  if (source.endsWith(".md")) return "📄";
  if (source.includes("glossario")) return "📖";
  if (source.includes("politica")) return "⚖️";
  if (source.includes("formula")) return "🔢";
  return "📁";
}

function getSourceLabel(source: string): string {
  return source.replace(/\.(md|txt|pdf)$/, "").replace(/_/g, " ");
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f2027 0%, #064e3b 100%)",
        borderRadius: "1rem",
        border: "1px solid #065f46",
        overflow: "hidden",
        boxShadow: "0 4px 24px rgba(16, 185, 129, 0.1)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.75rem 1rem",
          background: "rgba(16, 185, 129, 0.08)",
          borderBottom: "1px solid #065f46",
        }}
      >
        <span style={{ fontSize: "0.85rem" }}>📚</span>
        <span
          style={{
            color: "#34d399",
            fontWeight: 600,
            fontSize: "0.8rem",
            textTransform: "uppercase",
            letterSpacing: "0.1em",
          }}
        >
          Fontes
        </span>
        <span
          style={{
            background: "#064e3b",
            color: "#10b981",
            borderRadius: "9999px",
            padding: "0.1rem 0.5rem",
            fontSize: "0.7rem",
            fontWeight: 700,
            marginLeft: "auto",
          }}
        >
          {sources.length}
        </span>
      </div>

      {/* Sources list */}
      <ul
        style={{
          margin: 0,
          padding: "0.5rem",
          listStyle: "none",
          display: "flex",
          flexDirection: "column",
          gap: "0.25rem",
        }}
      >
        {sources.map((source, idx) => (
          <li
            key={idx}
            data-testid="source-item"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.5rem 0.75rem",
              background: "rgba(16, 185, 129, 0.05)",
              borderRadius: "0.5rem",
              border: "1px solid rgba(16, 185, 129, 0.1)",
              transition: "all 0.2s ease",
              cursor: "default",
            }}
          >
            <span style={{ fontSize: "0.9rem" }}>{getSourceIcon(source)}</span>
            <div>
              <div
                style={{
                  color: "#d1fae5",
                  fontSize: "0.8rem",
                  fontWeight: 500,
                }}
              >
                {source}
              </div>
              <div style={{ color: "#6ee7b7", fontSize: "0.7rem" }}>
                {getSourceLabel(source)}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

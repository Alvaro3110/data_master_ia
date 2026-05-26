"use client";
import { useState, useCallback } from "react";

interface SQLViewerProps {
  sql: string | null;
}

const SQL_KEYWORDS = [
  "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "LIMIT", "JOIN",
  "ON", "AS", "AND", "OR", "NOT", "IN", "WITH", "HAVING", "DISTINCT",
  "AVG", "SUM", "COUNT", "MAX", "MIN", "ROUND", "CASE", "WHEN", "THEN",
  "ELSE", "END", "INNER", "LEFT", "RIGHT", "OUTER", "UNION", "INSERT",
];

function highlightSQL(sql: string): React.ReactNode[] {
  const lines = sql.split("\n");
  return lines.map((line, lineIdx) => {
    const tokens = line.split(/(\s+|,|;|\(|\))/);
    const highlighted = tokens.map((token, i) => {
      const upper = token.trim().toUpperCase();
      if (SQL_KEYWORDS.includes(upper)) {
        return (
          <span key={i} style={{ color: "#7c3aed", fontWeight: 700 }}>
            {token}
          </span>
        );
      }
      if (/^'[^']*'$/.test(token)) {
        return (
          <span key={i} style={{ color: "#059669" }}>
            {token}
          </span>
        );
      }
      if (/^\d+$/.test(token)) {
        return (
          <span key={i} style={{ color: "#d97706" }}>
            {token}
          </span>
        );
      }
      return <span key={i}>{token}</span>;
    });
    return (
      <div key={lineIdx} style={{ display: "flex" }}>
        <span
          style={{
            color: "#6b7280",
            fontSize: "0.7rem",
            userSelect: "none",
            minWidth: "2rem",
            paddingRight: "0.75rem",
            textAlign: "right",
            borderRight: "1px solid #1f2937",
            marginRight: "0.75rem",
          }}
        >
          {lineIdx + 1}
        </span>
        <span>{highlighted}</span>
      </div>
    );
  });
}

export function SQLViewer({ sql }: SQLViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    if (!sql) return;
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [sql]);

  if (!sql) return null;

  const lineCount = sql.split("\n").length;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
        borderRadius: "1rem",
        border: "1px solid #312e81",
        overflow: "hidden",
        boxShadow: "0 4px 24px rgba(124, 58, 237, 0.15)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.75rem 1rem",
          background: "rgba(124, 58, 237, 0.1)",
          borderBottom: "1px solid #312e81",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.8rem" }}>🗄️</span>
          <span
            style={{
              color: "#a78bfa",
              fontWeight: 600,
              fontSize: "0.8rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            SQL Executado
          </span>
          <span
            style={{
              background: "#1e1b4b",
              color: "#7c3aed",
              borderRadius: "9999px",
              padding: "0.1rem 0.5rem",
              fontSize: "0.7rem",
              fontWeight: 700,
            }}
          >
            {lineCount} linhas
          </span>
        </div>
        <button
          onClick={handleCopy}
          aria-label={copied ? "Copiado!" : "Copiar SQL"}
          style={{
            background: copied ? "rgba(5, 150, 105, 0.2)" : "rgba(124, 58, 237, 0.2)",
            color: copied ? "#10b981" : "#a78bfa",
            border: `1px solid ${copied ? "#10b981" : "#7c3aed"}`,
            borderRadius: "0.5rem",
            padding: "0.25rem 0.75rem",
            fontSize: "0.75rem",
            cursor: "pointer",
            transition: "all 0.2s ease",
            fontWeight: 600,
          }}
        >
          {copied ? "✓ Copiado!" : "⎘ Copiar"}
        </button>
      </div>
      {/* Code */}
      <pre
        style={{
          margin: 0,
          padding: "1rem",
          overflowX: "auto",
          fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
          fontSize: "0.82rem",
          lineHeight: "1.7",
          color: "#e2e8f0",
          background: "transparent",
        }}
      >
        <code>{highlightSQL(sql)}</code>
      </pre>
    </div>
  );
}

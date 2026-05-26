import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Artifact {
  tipo: string;
  conteudo: string;
  titulo?: string;
}

interface ArtifactViewerProps {
  artifacts: Artifact[];
}

export function ArtifactViewer({ artifacts }: ArtifactViewerProps) {
  if (!artifacts || artifacts.length === 0) return null;

  return (
    <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      {artifacts.map((artifact, idx) => (
        <div
          key={idx}
          style={{
            background: "rgba(15, 23, 42, 0.4)",
            border: "1px solid rgba(148, 163, 184, 0.1)",
            borderRadius: "0.5rem",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              background: "rgba(15, 23, 42, 0.6)",
              padding: "0.5rem 1rem",
              borderBottom: "1px solid rgba(148, 163, 184, 0.1)",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              fontSize: "0.8rem",
              color: "#94a3b8",
              fontWeight: 600,
            }}
          >
            <span>📄</span>
            {artifact.titulo || "Relatório"}
          </div>
          <div style={{ padding: "1rem", fontSize: "0.85rem", color: "#f1f5f9", overflowX: "auto" }} className="prose prose-invert prose-sm max-w-none">
            {artifact.tipo === "markdown" ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.conteudo}</ReactMarkdown>
            ) : (
              <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {artifact.conteudo}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

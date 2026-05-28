"use client";
import { useState, useEffect, useCallback } from "react";

interface Workspace {
  id: string;
  nome: string;
  user_id: string;
  agent_md?: string;
  criado_em: string;
}

interface WorkspaceSidebarProps {
  userId: string;
  apiUrl: string;
  onSelectWorkspace: (ws: Workspace) => void;
  activeWorkspaceId?: string;
}

function unwrapData<T>(payload: unknown): T {
  if (
    payload &&
    typeof payload === "object" &&
    "data" in payload
  ) {
    return (payload as { data: T }).data;
  }
  throw new Error("Contrato inválido: envelope {trace_id, data} ausente.");
}

export function WorkspaceSidebar({
  userId,
  apiUrl,
  onSelectWorkspace,
  activeWorkspaceId,
}: WorkspaceSidebarProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const fetchWorkspaces = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/workspaces?user_id=${encodeURIComponent(userId)}`);
      if (res.ok) {
        const payload = await res.json();
        setWorkspaces(unwrapData<Workspace[]>(payload));
      }
    } finally {
      setLoading(false);
    }
  }, [apiUrl, userId]);

  useEffect(() => {
    fetchWorkspaces();
  }, [fetchWorkspaces]);

  const createWorkspace = async () => {
    setCreating(true);
    try {
      const now = new Date().toLocaleDateString("pt-BR", { month: "short", day: "numeric" });
      const res = await fetch(`${apiUrl}/api/v1/workspaces`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome: `Análise ${now}`, user_id: userId }),
      });
      if (res.ok) {
        await fetchWorkspaces();
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <aside
      style={{
        width: "260px",
        minWidth: "220px",
        background: "rgba(15, 15, 25, 0.95)",
        borderRight: "1px solid rgba(255,255,255,0.07)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        padding: "1rem 0",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "0 1rem 1rem",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "0.75rem",
          }}
        >
          <span
            style={{
              fontSize: "0.7rem",
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "#475569",
            }}
          >
            Workspaces
          </span>
        </div>

        <button
          onClick={createWorkspace}
          disabled={creating}
          style={{
            width: "100%",
            background: "linear-gradient(135deg, rgba(124,58,237,0.15), rgba(109,40,217,0.1))",
            border: "1px solid rgba(124,58,237,0.3)",
            borderRadius: "0.6rem",
            padding: "0.5rem 0.75rem",
            color: "#a78bfa",
            fontSize: "0.78rem",
            fontWeight: 600,
            cursor: creating ? "not-allowed" : "pointer",
            textAlign: "left",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background =
              "linear-gradient(135deg, rgba(124,58,237,0.3), rgba(109,40,217,0.2))";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background =
              "linear-gradient(135deg, rgba(124,58,237,0.15), rgba(109,40,217,0.1))";
          }}
        >
          <span style={{ fontSize: "1rem" }}>＋</span>
          {creating ? "Criando..." : "Nova análise"}
        </button>
      </div>

      {/* Workspace list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0.75rem 0" }}>
        {loading ? (
          <div
            style={{
              padding: "1.5rem 1rem",
              color: "#475569",
              fontSize: "0.78rem",
              textAlign: "center",
            }}
          >
            carregando...
          </div>
        ) : workspaces.length === 0 ? (
          <div
            style={{
              padding: "1.5rem 1rem",
              color: "#334155",
              fontSize: "0.78rem",
              textAlign: "center",
              lineHeight: 1.6,
            }}
          >
            Nenhuma análise ainda.
            <br />
            Clique em "Nova análise" para começar.
          </div>
        ) : (
          workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => onSelectWorkspace(ws)}
              style={{
                width: "100%",
                background:
                  activeWorkspaceId === ws.id
                    ? "rgba(124,58,237,0.15)"
                    : "transparent",
                border: "none",
                borderLeft:
                  activeWorkspaceId === ws.id
                    ? "3px solid #7c3aed"
                    : "3px solid transparent",
                padding: "0.6rem 1rem",
                color: activeWorkspaceId === ws.id ? "#c4b5fd" : "#64748b",
                fontSize: "0.78rem",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s ease",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              onMouseEnter={(e) => {
                if (activeWorkspaceId !== ws.id) {
                  (e.currentTarget as HTMLElement).style.background =
                    "rgba(255,255,255,0.04)";
                  (e.currentTarget as HTMLElement).style.color = "#94a3b8";
                }
              }}
              onMouseLeave={(e) => {
                if (activeWorkspaceId !== ws.id) {
                  (e.currentTarget as HTMLElement).style.background = "transparent";
                  (e.currentTarget as HTMLElement).style.color = "#64748b";
                }
              }}
            >
              <div style={{ fontWeight: 500, marginBottom: "0.1rem" }}>{ws.nome}</div>
              <div style={{ fontSize: "0.65rem", color: "#334155" }}>
                {new Date(ws.criado_em).toLocaleDateString("pt-BR")}
              </div>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}

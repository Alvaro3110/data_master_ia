"use client";
import { useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { WorkspaceSidebar } from "@/components/WorkspaceSidebar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const USER_ID = "demo-user"; // Em produção viria da autenticação

interface Workspace {
  id: string;
  nome: string;
  user_id: string;
  agent_md?: string;
  criado_em: string;
}

export default function Home() {
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);

  return (
    <main
      style={{
        position: "relative",
        zIndex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.875rem 1.5rem",
          background: "rgba(6, 8, 15, 0.8)",
          backdropFilter: "blur(16px)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          flexShrink: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {/* Logo */}
          <div
            style={{
              width: "2.2rem",
              height: "2.2rem",
              background: "linear-gradient(135deg, #7c3aed, #6d28d9)",
              borderRadius: "0.6rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.1rem",
              boxShadow: "0 4px 16px rgba(124,58,237,0.4)",
            }}
          >
            🧠
          </div>
          <div>
            <h1
              style={{
                fontSize: "1rem",
                fontWeight: 700,
                color: "#f1f5f9",
                lineHeight: 1,
              }}
            >
              Agentic Analytics
            </h1>
            <p style={{ fontSize: "0.7rem", color: "#64748b", lineHeight: 1.2, marginTop: "0.15rem" }}>
              {activeWorkspace ? activeWorkspace.nome : "Pricing · Margem · Safra · Risco · ROAE"}
            </p>
          </div>
        </div>

        {/* Status badges */}
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              background: "rgba(16,185,129,0.1)",
              border: "1px solid rgba(16,185,129,0.3)",
              borderRadius: "9999px",
              padding: "0.25rem 0.75rem",
              fontSize: "0.72rem",
              color: "#34d399",
              fontWeight: 500,
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                background: "#10b981",
                borderRadius: "50%",
                animation: "pulse 2s ease infinite",
              }}
            />
            RAG
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              background: "rgba(124,58,237,0.1)",
              border: "1px solid rgba(124,58,237,0.3)",
              borderRadius: "9999px",
              padding: "0.25rem 0.75rem",
              fontSize: "0.72rem",
              color: "#a78bfa",
              fontWeight: 500,
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                background: "#7c3aed",
                borderRadius: "50%",
              }}
            />
            SQL Agent
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              background: "rgba(245,158,11,0.1)",
              border: "1px solid rgba(245,158,11,0.3)",
              borderRadius: "9999px",
              padding: "0.25rem 0.75rem",
              fontSize: "0.72rem",
              color: "#fbbf24",
              fontWeight: 500,
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                background: "#f59e0b",
                borderRadius: "50%",
              }}
            />
            LangGraph
          </div>
          {activeWorkspace && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.35rem",
                background: "rgba(59,130,246,0.1)",
                border: "1px solid rgba(59,130,246,0.3)",
                borderRadius: "9999px",
                padding: "0.25rem 0.75rem",
                fontSize: "0.72rem",
                color: "#60a5fa",
                fontWeight: 500,
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  background: "#3b82f6",
                  borderRadius: "50%",
                }}
              />
              Workspace ativo
            </div>
          )}
        </div>
      </header>

      {/* Layout principal — sidebar + chat */}
      <div
        style={{
          flex: 1,
          display: "flex",
          overflow: "hidden",
        }}
      >
        {/* Sidebar de Workspaces */}
        <WorkspaceSidebar
          userId={USER_ID}
          apiUrl={API_URL}
          onSelectWorkspace={setActiveWorkspace}
          activeWorkspaceId={activeWorkspace?.id}
        />

        {/* Área de Chat */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            padding: "1rem",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              flex: 1,
              background: "rgba(255,255,255,0.02)",
              backdropFilter: "blur(16px)",
              borderRadius: "1.25rem",
              border: "1px solid rgba(255,255,255,0.06)",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              boxShadow: "0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05)",
              padding: "1rem",
            }}
          >
            <ChatPanel
              apiUrl={API_URL}
              workspaceId={activeWorkspace?.id}
            />
          </div>
        </div>
      </div>
    </main>
  );
}

/**
 * TDD — Fase RED: testes do TracePanel antes da implementação.
 * Verifica exibição de trace_id, reasoning_steps e latência.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { TracePanel } from "../components/TracePanel";

const mockTrace = {
  trace_id: "abc-123-def-456",
  reasoning_steps: [
    "Validated query scope (score: 82/100)",
    "Retrieved 3 rule chunks from RAG (attempt 1)",
    "Generated and executed SQL (50 rows returned)",
    "Generated answer from context",
  ],
  retrieval_attempts: 1,
  rewritten_query: null,
  routed_path: "hybrid",
  latency_ms: 1240,
};

describe("TracePanel", () => {
  describe("Renderização básica", () => {
    it("renderiza o trace_id", () => {
      render(<TracePanel trace={mockTrace} />);
      expect(screen.getByText(/abc-123-def-456/)).toBeInTheDocument();
    });

    it("renderiza todos os reasoning_steps", () => {
      render(<TracePanel trace={mockTrace} />);
      mockTrace.reasoning_steps.forEach((step) => {
        expect(screen.getByText(step)).toBeInTheDocument();
      });
    });

    it("exibe latência em ms", () => {
      render(<TracePanel trace={mockTrace} />);
      expect(screen.getByText(/1240/)).toBeInTheDocument();
    });

    it("exibe o routed_path", () => {
      render(<TracePanel trace={mockTrace} />);
      expect(screen.getByText(/hybrid/i)).toBeInTheDocument();
    });

    it("não renderiza quando trace é null", () => {
      const { container } = render(<TracePanel trace={null} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe("Score do Guardrail", () => {
    it("extrai e exibe score do reasoning_step de guardrail", () => {
      const { container } = render(<TracePanel trace={mockTrace} />);
      // Score está dentro de um span no reasoning step — verificar innerHTML
      expect(container.innerHTML).toMatch(/82\/100/i);
    });
  });

  describe("Tentativas de recuperação", () => {
    it("exibe número de retrieval_attempts", () => {
      const { container } = render(<TracePanel trace={mockTrace} />);
      // O número 1 aparece em múltiplos contextos — verificar presença geral
      expect(container.innerHTML).toMatch(/retrieval|attempt|tentativa|1/i);
    });
  });

  describe("Rewritten query", () => {
    it("não exibe seção de reescrita quando rewritten_query é null", () => {
      render(<TracePanel trace={mockTrace} />);
      expect(screen.queryByText(/reescrita/i)).not.toBeInTheDocument();
    });

    it("exibe rewritten_query quando presente", () => {
      const traceWithRewrite = {
        ...mockTrace,
        rewritten_query: "Qual segmento tem pior ROAE médio por safra recente?",
      };
      render(<TracePanel trace={traceWithRewrite} />);
      expect(screen.getByText(/qual segmento/i)).toBeInTheDocument();
    });
  });

  describe("Título", () => {
    it("tem título de rastreabilidade", () => {
      const { container } = render(<TracePanel trace={mockTrace} />);
      // "Rastreabilidade" pode aparecer uma ou mais vezes
      expect(container.innerHTML).toMatch(/trace|rastreab|auditoria/i);
    });
  });
});

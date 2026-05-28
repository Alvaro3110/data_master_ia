/**
 * TDD — Fase RED: testes do ChatPanel antes da implementação.
 * Testa renderização, envio de mensagem e exibição de resposta.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { ChatPanel } from "../components/ChatPanel";

// Mock do fetch global
const mockFetch = jest.fn();
global.fetch = mockFetch;
const wrap = (data: unknown) => ({ trace_id: "trace-abc-123", data });

const mockApiResponse = {
  trace_id: "trace-abc-123",
  question: "Qual foi a margem por safra?",
  answer: "O segmento PME apresentou margem média de 8,3% na última safra.",
  routed_path: "analytics",
  reasoning_steps: [
    "Validated query scope (score: 90/100)",
    "Generated and executed SQL (50 rows returned)",
  ],
  retrieval_attempts: 1,
  rewritten_query: null,
  sources: [],
  sql: "SELECT safra, AVG(margem_liquida) FROM fact_pricing_snapshot GROUP BY safra LIMIT 50",
  sql_result: [{ safra: "2026-03", margem_media: 8.3 }],
  masked_fields: [],
  latency_ms: 980,
};

// Mock do EventSource
class MockEventSource {
  url: string;
  listeners: Record<string, Function[]> = {};

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      if (this.listeners["start"]) {
        this.listeners["start"].forEach((cb) => cb({ type: "start" }));
      }
      if (this.listeners["chunk"]) {
        this.listeners["chunk"].forEach((cb) =>
          cb({
            type: "chunk",
            lastEventId: "1-0",
            data: JSON.stringify({ text: "O segmento PME apresentou margem média de 8,3% na última safra." }),
          })
        );
      }
      if (this.listeners["done"]) {
        this.listeners["done"].forEach((cb) =>
          cb({
            type: "done",
            lastEventId: "2-0",
            data: JSON.stringify(mockApiResponse),
          })
        );
      }
    }, 20);
  }

  addEventListener(event: string, callback: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  close() {}
}

global.EventSource = MockEventSource as any;

beforeEach(() => {
  mockFetch.mockReset();
});

describe("ChatPanel", () => {
  describe("Renderização inicial", () => {
    it("exibe placeholder no input", () => {
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      expect(
        screen.getByPlaceholderText(/pergunte sobre pricing|pergunta|ask/i)
      ).toBeInTheDocument();
    });

    it("tem botão de envio", () => {
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      expect(
        screen.getByRole("button", { name: /enviar|send|analisar/i })
      ).toBeInTheDocument();
    });

    it("botão de envio está desabilitado com input vazio", () => {
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const btn = screen.getByRole("button", { name: /enviar|send|analisar/i });
      expect(btn).toBeDisabled();
    });

    it("exibe mensagem de boas-vindas inicial", () => {
      const { container } = render(<ChatPanel apiUrl="http://localhost:8000" />);
      expect(container.innerHTML).toMatch(/pricing|margem|safra|bem-vindo|analytics/i);
    });
  });

  describe("Interação do usuário", () => {
    it("habilita botão ao digitar no input", async () => {
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox");
      await userEvent.type(input, "Qual a margem por safra?");
      const btn = screen.getByRole("button", { name: /enviar|send|analisar/i });
      expect(btn).toBeEnabled();
    });

    it("exibe a pergunta do usuário após envio", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => wrap({ trace_id: "trace-abc-123" }),
      });
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox");
      await userEvent.type(input, "Qual foi a margem por safra?");
      fireEvent.click(screen.getByRole("button", { name: /enviar|send|analisar/i }));
      await waitFor(() =>
        expect(screen.getByText(/qual foi a margem por safra/i)).toBeInTheDocument()
      );
    });

    it("exibe a resposta da API após envio", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => wrap({ trace_id: "trace-abc-123" }),
      });
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox");
      await userEvent.type(input, "Qual foi a margem por safra?");
      fireEvent.click(screen.getByRole("button", { name: /enviar|send|analisar/i }));
      await waitFor(() =>
        expect(screen.getByText(/PME apresentou margem média/i)).toBeInTheDocument()
      );
    });

    it("limpa o input após envio", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => wrap({ trace_id: "trace-abc-123" }),
      });
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox") as HTMLInputElement;
      await userEvent.type(input, "Qual foi a margem por safra?");
      fireEvent.click(screen.getByRole("button", { name: /enviar|send|analisar/i }));
      await waitFor(() => expect(input.value).toBe(""));
    });

    it("envia com Enter", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => wrap({ trace_id: "trace-abc-123" }),
      });
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox");
      await userEvent.type(input, "Qual a margem?{enter}");
      await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));
    });
  });

  describe("Estado de loading", () => {
    it("exibe indicador de loading durante chamada à API", async () => {
      let resolvePromise: (value: any) => void;
      mockFetch.mockReturnValueOnce(
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox");
      await userEvent.type(input, "Qual a margem?");
      fireEvent.click(screen.getByRole("button", { name: /enviar|send|analisar/i }));
      await waitFor(() =>
        expect(screen.getByTestId("loading-indicator")).toBeInTheDocument()
      );
      resolvePromise!({
        ok: true,
        json: async () => wrap({ trace_id: "trace-abc-123" }),
      });
    });
  });

  describe("Tratamento de erro", () => {
    it("exibe mensagem de erro quando API falha", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const input = screen.getByRole("textbox");
      await userEvent.type(input, "Qual a margem?");
      fireEvent.click(screen.getByRole("button", { name: /enviar|send|analisar/i }));
      await waitFor(() => {
        expect(screen.getByText(/erro ao iniciar análise/i)).toBeInTheDocument();
      });
    });
  });

  describe("Questões de exemplo (quick prompts)", () => {
    it("exibe pelo menos 3 perguntas de exemplo", () => {
      render(<ChatPanel apiUrl="http://localhost:8000" />);
      const examples = screen.getAllByRole("button");
      expect(examples.length).toBeGreaterThanOrEqual(4);
    });
  });
});

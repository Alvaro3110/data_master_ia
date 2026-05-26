/**
 * TDD — Fase RED: testes do SQLViewer antes da implementação.
 * Verifica renderização, syntax highlight e comportamento de copy.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { SQLViewer } from "../components/SQLViewer";

const sampleSQL = `SELECT segmento, AVG(margem_liquida) AS margem_media
FROM fact_pricing_snapshot
WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
GROUP BY segmento
ORDER BY margem_media
LIMIT 50`;

describe("SQLViewer", () => {
  describe("Renderização básica", () => {
    it("renderiza o SQL recebido como prop", () => {
      render(<SQLViewer sql={sampleSQL} />);
      // SQL pode estar dividido em spans — verificar presença no container
      const { container } = render(<SQLViewer sql={sampleSQL} />);
      expect(container.innerHTML).toMatch(/fact_pricing_snapshot/i);
    });

    it("exibe o label 'SQL Executado'", () => {
      render(<SQLViewer sql={sampleSQL} />);
      expect(screen.getByText(/sql executado/i)).toBeInTheDocument();
    });

    it("não renderiza nada quando sql é null", () => {
      const { container } = render(<SQLViewer sql={null} />);
      expect(container.firstChild).toBeNull();
    });

    it("não renderiza nada quando sql é string vazia", () => {
      const { container } = render(<SQLViewer sql="" />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe("Keywords SQL destacadas", () => {
    it("contém elemento pre ou code para o SQL", () => {
      const { container } = render(<SQLViewer sql={sampleSQL} />);
      const codeBlock = container.querySelector("pre, code");
      expect(codeBlock).toBeInTheDocument();
    });

    it("keywords SQL estão presentes no texto", () => {
      const { container } = render(<SQLViewer sql={sampleSQL} />);
      // Keywords são renderizadas em múltiplos spans — verificar innerHTML
      expect(container.innerHTML).toMatch(/SELECT/i);
      expect(container.innerHTML).toMatch(/FROM/i);
      expect(container.innerHTML).toMatch(/WHERE/i);
      // GROUP BY é tokenizado separadamente como GROUP e BY
      expect(container.innerHTML).toMatch(/GROUP/i);
      expect(container.innerHTML).toMatch(/LIMIT/i);
    });
  });

  describe("Botão de cópia", () => {
    it("tem um botão 'Copiar'", () => {
      render(<SQLViewer sql={sampleSQL} />);
      expect(screen.getByRole("button", { name: /copiar/i })).toBeInTheDocument();
    });

    it("botão de copiar chama clipboard.writeText", async () => {
      Object.assign(navigator, {
        clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
      });
      render(<SQLViewer sql={sampleSQL} />);
      fireEvent.click(screen.getByRole("button", { name: /copiar/i }));
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(sampleSQL);
    });

    it("mostra 'Copiado!' após clicar e reverte após 2s", async () => {
      jest.useFakeTimers();
      Object.assign(navigator, {
        clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
      });
      render(<SQLViewer sql={sampleSQL} />);
      fireEvent.click(screen.getByRole("button", { name: /copiar/i }));
      await waitFor(() =>
        expect(screen.getByRole("button")).toHaveTextContent(/copiado/i)
      );
      jest.advanceTimersByTime(2100);
      await waitFor(() =>
        expect(screen.getByRole("button")).toHaveTextContent(/copiar/i)
      );
      jest.useRealTimers();
    });
  });

  describe("Número de linhas", () => {
    it("exibe contagem de linhas do SQL", () => {
      const { container } = render(<SQLViewer sql={sampleSQL} />);
      const lineCount = sampleSQL.split("\n").length;
      // Número de linha pode aparecer em múltiplos spans (numeração)
      expect(container.innerHTML).toMatch(new RegExp(String(lineCount)));
    });
  });
});

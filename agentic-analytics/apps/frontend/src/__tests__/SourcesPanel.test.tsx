/**
 * TDD — Fase RED: testes do SourcesPanel antes da implementação.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { SourcesPanel } from "../components/SourcesPanel";

const mockSources = [
  "glossario_pricing.md",
  "politica_risco.md",
  "formula_roae.md",
];

describe("SourcesPanel", () => {
  describe("Renderização básica", () => {
    it("renderiza o título 'Fontes'", () => {
      render(<SourcesPanel sources={mockSources} />);
      expect(screen.getByText(/fontes/i)).toBeInTheDocument();
    });

    it("renderiza cada fonte como item de lista", () => {
      render(<SourcesPanel sources={mockSources} />);
      mockSources.forEach((src) => {
        expect(screen.getByText(src)).toBeInTheDocument();
      });
    });

    it("exibe contagem correta de fontes", () => {
      render(<SourcesPanel sources={mockSources} />);
      expect(screen.getByText(/3/)).toBeInTheDocument();
    });

    it("não renderiza quando sources é array vazio", () => {
      const { container } = render(<SourcesPanel sources={[]} />);
      expect(container.firstChild).toBeNull();
    });

    it("não renderiza quando sources é undefined", () => {
      const { container } = render(<SourcesPanel sources={undefined as any} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe("Ícone de documento", () => {
    it("tem um ícone ou indicador por fonte", () => {
      const { container } = render(<SourcesPanel sources={mockSources} />);
      const items = container.querySelectorAll("li, [data-testid='source-item']");
      expect(items.length).toBeGreaterThanOrEqual(mockSources.length);
    });
  });

  describe("Tipo de fonte", () => {
    it("identifica fontes .md como documentação", () => {
      render(<SourcesPanel sources={["glossario.md"]} />);
      expect(screen.getByText(/glossario\.md/i)).toBeInTheDocument();
    });
  });
});

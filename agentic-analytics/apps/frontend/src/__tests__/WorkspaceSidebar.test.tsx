import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { WorkspaceSidebar } from "../components/WorkspaceSidebar";

// Mock da fetch API
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockWorkspaces = [
  { id: "ws-1", nome: "Análise Safra 2026-03", user_id: "u1", agent_md: "", criado_em: "2026-05-26T00:00:00Z" },
  { id: "ws-2", nome: "Pricing PME Q2", user_id: "u1", agent_md: "", criado_em: "2026-05-25T00:00:00Z" },
];

const wrap = (data: unknown) => ({ trace_id: "trace-test", data });

describe("WorkspaceSidebar", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renderiza título do painel", () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => wrap([]),
    });
    const { container } = render(
      <WorkspaceSidebar userId="u1" apiUrl="http://localhost:8001" onSelectWorkspace={jest.fn()} />
    );
    expect(container.innerHTML).toContain("Workspaces");
  });

  it("lista workspaces carregados da API", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => wrap(mockWorkspaces),
    });
    const { container } = render(
      <WorkspaceSidebar userId="u1" apiUrl="http://localhost:8001" onSelectWorkspace={jest.fn()} />
    );
    await waitFor(() => {
      expect(container.innerHTML).toContain("Safra 2026-03");
      expect(container.innerHTML).toContain("Pricing PME Q2");
    });
  });

  it("chama onSelectWorkspace ao clicar em um workspace", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => wrap(mockWorkspaces),
    });
    const onSelect = jest.fn();
    render(
      <WorkspaceSidebar userId="u1" apiUrl="http://localhost:8001" onSelectWorkspace={onSelect} />
    );
    await waitFor(() => screen.getByText("Análise Safra 2026-03"));
    fireEvent.click(screen.getByText("Análise Safra 2026-03"));
    expect(onSelect).toHaveBeenCalledWith(mockWorkspaces[0]);
  });

  it("exibe botão de novo workspace", () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => wrap([]) });
    const { container } = render(
      <WorkspaceSidebar userId="u1" apiUrl="http://localhost:8001" onSelectWorkspace={jest.fn()} />
    );
    expect(container.innerHTML).toContain("Nova análise");
  });

  it("cria workspace ao clicar em Nova análise", async () => {
    // GET retorna lista vazia, depois POST cria, depois GET retorna o novo
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => wrap([]) })
      .mockResolvedValueOnce({ ok: true, json: async () => wrap({ id: "ws-new", nome: "Nova Análise", user_id: "u1", criado_em: "2026-05-26T00:00:00Z" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => wrap([{ id: "ws-new", nome: "Nova Análise", user_id: "u1", criado_em: "2026-05-26T00:00:00Z" }]) });

    render(
      <WorkspaceSidebar userId="u1" apiUrl="http://localhost:8001" onSelectWorkspace={jest.fn()} />
    );

    await waitFor(() => screen.getByText("Nova análise"));
    fireEvent.click(screen.getByText("Nova análise"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/workspaces"),
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  it("mostra estado de carregamento", () => {
    mockFetch.mockImplementationOnce(() => new Promise(() => {})); // nunca resolve
    const { container } = render(
      <WorkspaceSidebar userId="u1" apiUrl="http://localhost:8001" onSelectWorkspace={jest.fn()} />
    );
    expect(container.innerHTML).toContain("carregando") || expect(container.innerHTML).toContain("...");
  });
});

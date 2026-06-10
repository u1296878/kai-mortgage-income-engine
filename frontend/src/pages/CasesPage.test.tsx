import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { CasesPage } from "./CasesPage";

const caseApi = vi.hoisted(() => ({
  createCase: vi.fn(),
  listCases: vi.fn(),
}));

vi.mock("../api/cases", () => ({
  createCase: caseApi.createCase,
  listCases: caseApi.listCases,
}));

describe("CasesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    caseApi.listCases.mockResolvedValue([
      {
        id: "case-1",
        broker_id: "broker-1",
        title: "Johnson Refi",
        status: "open",
        created_at: "2026-05-31T00:00:00Z",
        updated_at: "2026-05-31T00:00:00Z",
      },
    ]);
    caseApi.createCase.mockResolvedValue({
      id: "case-2",
      broker_id: "broker-1",
      title: "New purchase",
      status: "open",
      created_at: "2026-05-31T00:00:00Z",
      updated_at: "2026-05-31T00:00:00Z",
    });
  });

  it("renders case cards", async () => {
    renderWithQueryClient(
      <MemoryRouter>
        <CasesPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Johnson Refi")).toBeInTheDocument();
    expect(screen.queryByText("Broker ID: broker-1")).not.toBeInTheDocument();
  });

  it("creates a new case from the form", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <CasesPage />
      </MemoryRouter>,
    );

    await screen.findByText("Johnson Refi");
    await user.click(screen.getByRole("button", { name: "New Case" }));
    await user.type(screen.getByPlaceholderText("Case title"), "New purchase");
    await user.click(screen.getByRole("button", { name: "Create case" }));

    await waitFor(() => {
      expect(caseApi.createCase).toHaveBeenCalledWith("New purchase");
    });
  });
});

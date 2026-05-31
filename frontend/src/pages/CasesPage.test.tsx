import { screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { CasesPage } from "./CasesPage";

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: "u-1", email: "manager@example.com", role: "manager" },
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("../api/cases", () => ({
  listCases: vi.fn().mockResolvedValue([
    {
      id: "case-1",
      broker_id: "broker-1",
      title: "Johnson Refi",
      status: "open",
      created_at: "2026-05-31T00:00:00Z",
      updated_at: "2026-05-31T00:00:00Z",
    },
  ]),
}));

describe("CasesPage", () => {
  it("renders case cards", async () => {
    renderWithQueryClient(
      <MemoryRouter>
        <CasesPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Johnson Refi")).toBeInTheDocument();
    expect(screen.getByText("Broker ID: broker-1")).toBeInTheDocument();
  });
});

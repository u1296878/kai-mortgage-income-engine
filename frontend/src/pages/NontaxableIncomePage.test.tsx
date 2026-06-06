import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { NontaxableIncomePage } from "./NontaxableIncomePage";

const incomeApi = vi.hoisted(() => ({
  calculateNontaxableIncome: vi.fn(),
  saveNontaxableCalculation: vi.fn(),
}));

vi.mock("../api/income", () => ({
  calculateNontaxableIncome: incomeApi.calculateNontaxableIncome,
  saveNontaxableCalculation: incomeApi.saveNontaxableCalculation,
}));

describe("NontaxableIncomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    incomeApi.calculateNontaxableIncome.mockResolvedValue({
      monthly: 2000,
      method: "gross_100",
      taxable_monthly: 2000,
      eligible_monthly: 0,
    });
    incomeApi.saveNontaxableCalculation.mockResolvedValue({
      id: "ntcalc-1",
      case_id: "case-1",
      borrower_id: null,
      label: "SSI",
      kind: "social_security",
      monthly: 1037.5,
      annual_income: 12450,
      breakdown: {},
      created_at: "2026-05-31T00:00:00Z",
    });
  });

  it("previews a non-taxable income source", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <NontaxableIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Annual gross"), "24000");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateNontaxableIncome).toHaveBeenCalledTimes(1);
    });
    expect(await screen.findByText("Qualifying monthly income:")).toBeInTheDocument();
    expect(screen.getAllByText("$2,000.00").length).toBeGreaterThan(0);
  });

  it("previews a Social Security source", async () => {
    const user = userEvent.setup();
    incomeApi.calculateNontaxableIncome.mockResolvedValue({
      monthly: 1037.5,
      method: "adjusted",
      taxable_monthly: 1000,
      eligible_monthly: 37.5,
    });
    renderWithQueryClient(
      <MemoryRouter>
        <NontaxableIncomePage />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText("Source kind"), "social_security");
    await user.selectOptions(screen.getByLabelText("Method"), "adjusted");
    await user.type(screen.getByLabelText("Annual gross"), "12000");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateNontaxableIncome).toHaveBeenCalledTimes(1);
    });
    const payload = incomeApi.calculateNontaxableIncome.mock.calls[0][0];
    expect(payload.kind).toBe("social_security");
    expect(payload.social_security.annual_gross).toBe(12000);
    expect(await screen.findByText("Qualifying monthly income:")).toBeInTheDocument();
    expect(screen.getByText("$1,037.50")).toBeInTheDocument();
  });

  it("saves the worksheet to a case when opened in a case context", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/income/nontaxable?caseId=case-1"]}>
        <NontaxableIncomePage />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText("Source kind"), "social_security");
    await user.type(screen.getByLabelText("Annual gross"), "12000");
    await user.type(screen.getByLabelText("Calculation label"), "SSI");
    await user.click(screen.getByRole("button", { name: "Save to case" }));

    await waitFor(() => {
      expect(incomeApi.saveNontaxableCalculation).toHaveBeenCalledTimes(1);
    });
    const [caseId, payload] = incomeApi.saveNontaxableCalculation.mock.calls[0];
    expect(caseId).toBe("case-1");
    expect(payload.kind).toBe("social_security");
    expect(payload.label).toBe("SSI");
  });
});

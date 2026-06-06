import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { EmploymentIncomePage } from "./EmploymentIncomePage";

const incomeApi = vi.hoisted(() => ({
  calculateEmploymentIncome: vi.fn(),
  saveEmploymentCalculation: vi.fn(),
}));

vi.mock("../api/income", () => ({
  calculateEmploymentIncome: incomeApi.calculateEmploymentIncome,
  saveEmploymentCalculation: incomeApi.saveEmploymentCalculation,
}));

function emptyBucket() {
  return {
    qualifying_monthly: 0,
    rate_of_pay_monthly: 0,
    periods: [],
  };
}

describe("EmploymentIncomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    incomeApi.saveEmploymentCalculation.mockResolvedValue({
      id: "calc-1",
      case_id: "case-1",
      borrower_id: null,
      label: "Acme Corp",
      total_monthly: 7000,
      annual_income: 84000,
      breakdown: {},
      created_at: "2026-05-31T00:00:00Z",
    });
    incomeApi.calculateEmploymentIncome.mockResolvedValue({
      base_pay: {
        qualifying_monthly: 5000,
        rate_of_pay_monthly: 0,
        periods: [{ months: 3.5, monthly: 5000, pct_change: null }],
      },
      overtime: emptyBucket(),
      bonus: emptyBucket(),
      commission: emptyBucket(),
      other: emptyBucket(),
      total_monthly: 7000,
    });
  });

  it("submits the worksheet and renders the returned total", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <EmploymentIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Base pay YTD from"), "2026-01-01");
    await user.type(screen.getByLabelText("Base pay YTD through"), "2026-04-15");
    await user.type(screen.getByLabelText("Base pay YTD earnings"), "17500");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateEmploymentIncome).toHaveBeenCalledTimes(1);
    });
    expect(
      await screen.findByText(/Total qualifying monthly income: \$7,000\.00/),
    ).toBeInTheDocument();
  });

  it("sends the chosen A/Y toggle for variable buckets", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <EmploymentIncomePage />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText("Overtime YTD method"), "A");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateEmploymentIncome).toHaveBeenCalledTimes(1);
    });
    const payload = incomeApi.calculateEmploymentIncome.mock.calls[0][0];
    expect(payload.overtime.annualize).toBe(true);
    expect(payload.overtime.use_ytd).toBe(false);
  });

  it("saves the worksheet to a case when opened in a case context", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/income/employment?caseId=case-1"]}>
        <EmploymentIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Base pay YTD from"), "2026-01-01");
    await user.type(screen.getByLabelText("Base pay YTD through"), "2026-04-15");
    await user.type(screen.getByLabelText("Base pay YTD earnings"), "17500");
    await user.type(screen.getByLabelText("Calculation label"), "Acme Corp");
    await user.click(screen.getByRole("button", { name: "Save to case" }));

    await waitFor(() => {
      expect(incomeApi.saveEmploymentCalculation).toHaveBeenCalledTimes(1);
    });
    const [caseId, payload] = incomeApi.saveEmploymentCalculation.mock.calls[0];
    expect(caseId).toBe("case-1");
    expect(payload.label).toBe("Acme Corp");
  });
});

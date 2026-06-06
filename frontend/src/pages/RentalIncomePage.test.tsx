import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { RentalIncomePage } from "./RentalIncomePage";

const incomeApi = vi.hoisted(() => ({
  calculateRentalIncome: vi.fn(),
  saveRentalCalculation: vi.fn(),
}));

vi.mock("../api/income", () => ({
  calculateRentalIncome: incomeApi.calculateRentalIncome,
  saveRentalCalculation: incomeApi.saveRentalCalculation,
}));

describe("RentalIncomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    incomeApi.calculateRentalIncome.mockResolvedValue({
      qualifying_monthly: 1125,
      property_class: "primary_2_4_unit",
      method: "schedule_e",
      years: [{ months: 12, annual_net: 14000, monthly_gross: 1166.67 }],
    });
    incomeApi.saveRentalCalculation.mockResolvedValue({
      id: "calc-1",
      case_id: "case-1",
      borrower_id: null,
      label: "123 Main St",
      qualifying_monthly: 1125,
      annual_income: 13500,
      breakdown: {},
      created_at: "2026-05-31T00:00:00Z",
    });
  });

  it("previews the rental worksheet and renders the qualifying figure", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <RentalIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Current year Rents received"), "24000");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateRentalIncome).toHaveBeenCalledTimes(1);
    });
    expect(
      await screen.findByText(/Qualifying monthly income: \$1,125\.00/),
    ).toBeInTheDocument();
  });

  it("sends lease fields when the lease method is selected", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <RentalIncomePage />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText("Method"), "lease");
    await user.type(screen.getByLabelText("Gross monthly rent"), "2000");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateRentalIncome).toHaveBeenCalledTimes(1);
    });
    const payload = incomeApi.calculateRentalIncome.mock.calls[0][0];
    expect(payload.method).toBe("lease");
    expect(payload.gross_monthly_rent).toBe(2000);
    expect(payload.schedule_e_years).toEqual([]);
  });

  it("saves the worksheet to a case when opened in a case context", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/income/rental?caseId=case-1"]}>
        <RentalIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Current year Rents received"), "24000");
    await user.type(screen.getByLabelText("Calculation label"), "123 Main St");
    await user.click(screen.getByRole("button", { name: "Save to case" }));

    await waitFor(() => {
      expect(incomeApi.saveRentalCalculation).toHaveBeenCalledTimes(1);
    });
    const [caseId, payload] = incomeApi.saveRentalCalculation.mock.calls[0];
    expect(caseId).toBe("case-1");
    expect(payload.label).toBe("123 Main St");
  });
});

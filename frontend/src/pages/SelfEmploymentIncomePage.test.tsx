import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { SelfEmploymentIncomePage } from "./SelfEmploymentIncomePage";

const incomeApi = vi.hoisted(() => ({
  calculateSelfEmployment: vi.fn(),
  saveSelfEmploymentCalculation: vi.fn(),
}));

vi.mock("../api/income", () => ({
  calculateSelfEmployment: incomeApi.calculateSelfEmployment,
  saveSelfEmploymentCalculation: incomeApi.saveSelfEmploymentCalculation,
}));

describe("SelfEmploymentIncomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    incomeApi.calculateSelfEmployment.mockResolvedValue({
      kind: "schedule_c",
      qualifying_monthly: 4166.67,
      annual_income: 50000.04,
      breakdown: {},
    });
    incomeApi.saveSelfEmploymentCalculation.mockResolvedValue({
      id: "secalc-1",
      case_id: "case-1",
      borrower_id: null,
      label: "Design LLC",
      kind: "schedule_c",
      qualifying_monthly: 4166.67,
      annual_income: 50000.04,
      breakdown: {},
      created_at: "2026-05-31T00:00:00Z",
    });
  });

  it("previews a personal schedule and normalizes blanks to zero", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <SelfEmploymentIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Schedule C year 1 Net profit"), "50000");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateSelfEmployment).toHaveBeenCalledTimes(1);
    });
    const payload = incomeApi.calculateSelfEmployment.mock.calls[0][0];
    expect(payload.kind).toBe("schedule_c");
    expect(payload.payload.years[0].net_profit).toBe(50000);
    expect(payload.payload.years[0].nonrecurring_income).toBe(0);
    expect(await screen.findByText("Qualifying monthly")).toBeInTheDocument();
  });

  it("previews an entity calculation", async () => {
    const user = userEvent.setup();
    incomeApi.calculateSelfEmployment.mockResolvedValue({
      kind: "partnership",
      qualifying_monthly: 7000,
      annual_income: 84000,
      breakdown: {},
    });
    renderWithQueryClient(
      <MemoryRouter>
        <SelfEmploymentIncomePage />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText("Self-employment kind"), "partnership");
    await user.type(screen.getByLabelText("Partnership K-1 year 1 Ordinary income"), "60000");
    await user.type(screen.getByLabelText("W-2 wages year 1 Wages"), "24000");
    await user.click(screen.getByRole("button", { name: "Calculate" }));

    await waitFor(() => {
      expect(incomeApi.calculateSelfEmployment).toHaveBeenCalledTimes(1);
    });
    const payload = incomeApi.calculateSelfEmployment.mock.calls[0][0];
    expect(payload.kind).toBe("partnership");
    expect(payload.payload.k1_years[0].ordinary_income).toBe(60000);
    expect(payload.payload.w2_years[0].wages).toBe(24000);
  });

  it("saves the worksheet to a case when opened in a case context", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/income/self-employment?caseId=case-1"]}>
        <SelfEmploymentIncomePage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Schedule C year 1 Net profit"), "50000");
    await user.type(screen.getByLabelText("Calculation label"), "Design LLC");
    await user.click(screen.getByRole("button", { name: "Save to case" }));

    await waitFor(() => {
      expect(incomeApi.saveSelfEmploymentCalculation).toHaveBeenCalledTimes(1);
    });
    const [caseId, payload] = incomeApi.saveSelfEmploymentCalculation.mock.calls[0];
    expect(caseId).toBe("case-1");
    expect(payload.kind).toBe("schedule_c");
    expect(payload.label).toBe("Design LLC");
  });
});

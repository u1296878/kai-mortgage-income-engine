import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { CaseDetailPage } from "./CaseDetailPage";

const caseApi = vi.hoisted(() => ({
  deleteCase: vi.fn(),
  getCase: vi.fn(),
  getCaseDocuments: vi.fn(),
  updateCaseStatus: vi.fn(),
}));
const incomeApi = vi.hoisted(() => ({
  deleteEmploymentCalculation: vi.fn(),
  deleteNontaxableCalculation: vi.fn(),
  deleteRentalCalculation: vi.fn(),
}));

vi.mock("../api/cases", () => caseApi);
vi.mock("../api/documents", () => ({
  deleteDocument: vi.fn(),
  unlinkDocumentFromCase: vi.fn(),
  uploadDocument: vi.fn(),
}));
vi.mock("../api/income", () => incomeApi);
vi.mock("../api/incomeStreams", () => ({ listCaseIncomeStreams: vi.fn().mockResolvedValue([]) }));
vi.mock("../api/borrowers", () => ({ listCaseBorrowers: vi.fn().mockResolvedValue([]) }));
vi.mock("../api/jobs", () => ({
  getDocumentJob: vi.fn(),
  retryJob: vi.fn(),
  waitForJobCompletion: vi.fn(),
}));
vi.mock("../api/results", () => ({
  getCaseSummary: vi.fn().mockResolvedValue({
    case_id: "case-1",
    total_annual_income: 97500,
    borrowers: [],
    income_streams: [],
    employment_calculations: [
      {
        id: "calc-1",
        case_id: "case-1",
        borrower_id: null,
        label: "Acme Corp",
        total_monthly: 7000,
        annual_income: 84000,
        breakdown: {},
        created_at: "2026-05-31T00:00:00Z",
      },
    ],
    rental_calculations: [
      {
        id: "rcalc-1",
        case_id: "case-1",
        borrower_id: null,
        label: "123 Main St",
        qualifying_monthly: 1125,
        annual_income: 13500,
        breakdown: {},
        created_at: "2026-05-31T00:00:00Z",
      },
    ],
    nontaxable_calculations: [],
    results: [],
    sources: [],
  }),
  getJobResult: vi.fn(),
}));

function renderPage(): void {
  renderWithQueryClient(
    <MemoryRouter initialEntries={["/cases/case-1"]}>
      <Routes>
        <Route path="/cases/:caseId" element={<CaseDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("CaseDetailPage calculation panels", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    caseApi.deleteCase.mockResolvedValue(undefined);
    caseApi.getCase.mockResolvedValue({
      id: "case-1",
      broker_id: "broker-1",
      title: "Taylor Purchase",
      status: "open",
      created_at: "2026-05-31T00:00:00Z",
      updated_at: "2026-05-31T00:00:00Z",
    });
    caseApi.getCaseDocuments.mockResolvedValue({ documents: [] });
  });

  it("lists and deletes a saved employment calculation", async () => {
    const user = userEvent.setup();
    incomeApi.deleteEmploymentCalculation.mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText(/\$84,000\.00\/yr/)).toBeInTheDocument();
    const panel = screen.getByText("Employment Income").closest("section") as HTMLElement;
    await user.click(within(panel).getByRole("button", { name: "Delete" }));

    expect(incomeApi.deleteEmploymentCalculation).toHaveBeenCalledWith("case-1", "calc-1");
  });

  it("lists and deletes a saved rental calculation", async () => {
    const user = userEvent.setup();
    incomeApi.deleteRentalCalculation.mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findByText("123 Main St")).toBeInTheDocument();
    expect(screen.getByText(/\$13,500\.00\/yr/)).toBeInTheDocument();
    const panel = screen.getByText("Rental Income").closest("section") as HTMLElement;
    await user.click(within(panel).getByRole("button", { name: "Delete" }));

    expect(incomeApi.deleteRentalCalculation).toHaveBeenCalledWith("case-1", "rcalc-1");
  });
});

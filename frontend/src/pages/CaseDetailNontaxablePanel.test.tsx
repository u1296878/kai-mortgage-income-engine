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
    total_annual_income: 12450,
    borrowers: [],
    income_streams: [],
    employment_calculations: [],
    rental_calculations: [],
    nontaxable_calculations: [
      {
        id: "ntcalc-1",
        case_id: "case-1",
        borrower_id: null,
        label: "SSI",
        kind: "social_security",
        monthly: 1037.5,
        annual_income: 12450,
        breakdown: {},
        created_at: "2026-05-31T00:00:00Z",
      },
    ],
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

describe("CaseDetailPage non-taxable panel", () => {
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
    incomeApi.deleteNontaxableCalculation.mockResolvedValue(undefined);
  });

  it("lists and deletes a saved non-taxable calculation", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("SSI")).toBeInTheDocument();
    expect(screen.getByText(/Social Security/)).toBeInTheDocument();
    const panel = screen.getByText("Non-taxable Income").closest("section") as HTMLElement;
    await user.click(within(panel).getByRole("button", { name: "Delete" }));

    expect(incomeApi.deleteNontaxableCalculation).toHaveBeenCalledWith(
      "case-1",
      "ntcalc-1",
    );
  });
});

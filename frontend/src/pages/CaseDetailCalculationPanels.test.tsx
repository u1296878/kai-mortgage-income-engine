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
  deleteSelfEmploymentCalculation: vi.fn(),
  updateRentalCalculation: vi.fn(),
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
        inputs: {
          property_class: "primary_2_4_unit",
          method: "schedule_e",
          schedule_e_years: [],
          monthly_pitia: null,
          gross_monthly_rent: null,
          vacancy_factor: 0.25,
        },
        qualifying_monthly: 1125,
        annual_income: 13500,
        included: true,
        source_document_id: "doc-1",
        source_property_key: "a",
        breakdown: {},
        created_at: "2026-05-31T00:00:00Z",
      },
    ],
    nontaxable_calculations: [],
    self_employment_calculations: [
      {
        id: "secalc-1",
        case_id: "case-1",
        borrower_id: null,
        label: "Design LLC",
        kind: "schedule_c",
        qualifying_monthly: 4166.67,
        annual_income: 50000.04,
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

  it("updates rental calculation inclusion", async () => {
    const user = userEvent.setup();
    incomeApi.updateRentalCalculation.mockResolvedValue(undefined);
    renderPage();

    const panel = (await screen.findByText("Rental Income")).closest("section") as HTMLElement;
    await user.click(within(panel).getByRole("checkbox", { name: "Included" }));

    expect(incomeApi.updateRentalCalculation).toHaveBeenCalledWith("case-1", "rcalc-1", { included: false });
  });

  it("lists and deletes a saved self-employment calculation", async () => {
    const user = userEvent.setup();
    incomeApi.deleteSelfEmploymentCalculation.mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findByText("Design LLC")).toBeInTheDocument();
    expect(screen.getByText(/\$50,000\.04\/yr/)).toBeInTheDocument();
    const panel = screen.getByText("Self-employment Income").closest("section") as HTMLElement;
    await user.click(within(panel).getByRole("button", { name: "Delete" }));

    expect(incomeApi.deleteSelfEmploymentCalculation).toHaveBeenCalledWith(
      "case-1",
      "secalc-1",
    );
  });
});

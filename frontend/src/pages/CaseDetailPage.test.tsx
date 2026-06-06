import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getDocumentJob } from "../api/jobs";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { CaseDetailPage } from "./CaseDetailPage";

const caseApi = vi.hoisted(() => ({
  deleteCase: vi.fn(),
  getCase: vi.fn(),
  getCaseDocuments: vi.fn(),
  updateCaseStatus: vi.fn(),
}));

vi.mock("../api/cases", () => ({
  deleteCase: caseApi.deleteCase,
  getCase: caseApi.getCase,
  getCaseDocuments: caseApi.getCaseDocuments,
  updateCaseStatus: caseApi.updateCaseStatus,
}));

vi.mock("../api/documents", () => ({
  deleteDocument: vi.fn(),
  unlinkDocumentFromCase: vi.fn(),
  uploadDocument: vi.fn(),
}));

const incomeApi = vi.hoisted(() => ({ deleteEmploymentCalculation: vi.fn() }));

vi.mock("../api/income", () => ({
  deleteEmploymentCalculation: incomeApi.deleteEmploymentCalculation,
}));

vi.mock("../api/results", () => ({
  getCaseSummary: vi.fn().mockResolvedValue({
    case_id: "case-1",
    total_annual_income: 87638,
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
    results: [
      {
        id: "result-1",
        job_id: "job-1",
        document_id: "doc-1",
        case_id: "case-1",
        income_stream_id: null,
        doc_type: "tax_return",
        extracted_fields: [
          {
            field: "agi",
            value: 87638,
            document_id: "doc-1",
            page: 1,
            bounding_box: { x1: 10, y1: 20, x2: 30, y2: 40 },
          },
        ],
        annual_income: 87638,
        confidence: "high",
        notes: null,
        created_at: "2026-05-31T00:00:00Z",
      },
    ],
    sources: [],
  }),
  getJobResult: vi.fn(),
}));

vi.mock("../api/incomeStreams", () => ({
  listCaseIncomeStreams: vi.fn().mockResolvedValue([]),
}));

vi.mock("../api/borrowers", () => ({
  listCaseBorrowers: vi.fn().mockResolvedValue([]),
}));

vi.mock("../api/jobs", () => ({
  getDocumentJob: vi.fn().mockResolvedValue({
    id: "job-1",
    status: "complete",
    error: null,
    created_at: "2026-05-31T00:00:00Z",
    started_at: "2026-05-31T00:00:00Z",
    completed_at: "2026-05-31T00:00:00Z",
  }),
  retryJob: vi.fn(),
  waitForJobCompletion: vi.fn(),
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

describe("CaseDetailPage", () => {
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
    caseApi.getCaseDocuments.mockResolvedValue({
      id: "case-1",
      broker_id: "broker-1",
      title: "Taylor Purchase",
      status: "open",
      created_at: "2026-05-31T00:00:00Z",
      updated_at: "2026-05-31T00:00:00Z",
      documents: [
        {
          id: "doc-1",
          filename: "w2.pdf",
          doc_type: "w2",
          case_id: "case-1",
          uploaded_at: "2026-05-31T00:00:00Z",
        },
        {
          id: "doc-2",
          filename: "paystub.pdf",
          doc_type: "pay_stub",
          case_id: "case-1",
          uploaded_at: "2026-05-31T00:00:00Z",
        },
      ],
    });
  });

  it("renders extracted fields and source references", async () => {
    renderPage();

    expect(await screen.findByText("Taylor Purchase")).toBeInTheDocument();
    expect(screen.getByText("agi")).toBeInTheDocument();
    expect(screen.getByText(/Source: page 1/)).toBeInTheDocument();
    const calls = vi.mocked(getDocumentJob).mock.calls;
    expect(calls).toHaveLength(1);
    expect(calls[0][0]).toBe("doc-2");
  });

  it("lists and deletes a saved employment calculation", async () => {
    const user = userEvent.setup();
    incomeApi.deleteEmploymentCalculation.mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("$7,000.00/mo · $84,000.00/yr")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(incomeApi.deleteEmploymentCalculation).toHaveBeenCalledWith("case-1", "calc-1");
  });

  it("does not delete a case when confirmation is cancelled", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    renderPage();

    await screen.findByText("Taylor Purchase");
    await user.click(screen.getByRole("button", { name: "Delete case" }));

    expect(confirmSpy).toHaveBeenCalled();
    expect(caseApi.deleteCase).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });
});

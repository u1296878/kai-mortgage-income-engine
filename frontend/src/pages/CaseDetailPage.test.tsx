import { screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { CaseDetailPage } from "./CaseDetailPage";

vi.mock("../api/cases", () => ({
  getCase: vi.fn().mockResolvedValue({
    id: "case-1",
    broker_id: "broker-1",
    title: "Taylor Purchase",
    status: "open",
    created_at: "2026-05-31T00:00:00Z",
    updated_at: "2026-05-31T00:00:00Z",
  }),
  getCaseDocuments: vi.fn().mockResolvedValue({
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
    ],
  }),
}));

vi.mock("../api/results", () => ({
  getCaseSummary: vi.fn().mockResolvedValue({
    case_id: "case-1",
    total_annual_income: 87638,
    borrowers: [],
    income_streams: [],
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
  waitForJobCompletion: vi.fn(),
}));

describe("CaseDetailPage", () => {
  it("renders extracted fields and source references", async () => {
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/cases/case-1"]}>
        <Routes>
          <Route path="/cases/:caseId" element={<CaseDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Taylor Purchase")).toBeInTheDocument();
    expect(screen.getByText("agi")).toBeInTheDocument();
    expect(screen.getByText(/Source: page 1/)).toBeInTheDocument();
  });
});

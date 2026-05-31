import { apiRequest } from "./client";
import type { CaseSummaryResponse, ResultResponse } from "../types/api";

export function getJobResult(jobId: string): Promise<ResultResponse> {
  return apiRequest<ResultResponse>(`/jobs/${jobId}/result`);
}

export function getCaseSummary(caseId: string): Promise<CaseSummaryResponse> {
  return apiRequest<CaseSummaryResponse>(`/cases/${caseId}/summary`);
}

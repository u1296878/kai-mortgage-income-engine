import { apiRequest } from "./client";
import type { IncomeStreamResponse } from "../types/api";

export function listCaseIncomeStreams(caseId: string): Promise<IncomeStreamResponse[]> {
  return apiRequest<IncomeStreamResponse[]>(`/cases/${caseId}/income-streams`);
}

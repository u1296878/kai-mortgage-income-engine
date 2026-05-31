import { apiRequest } from "./client";
import type { BorrowerResponse } from "../types/api";

export function listCaseBorrowers(caseId: string): Promise<BorrowerResponse[]> {
  return apiRequest<BorrowerResponse[]>(`/cases/${caseId}/borrowers`);
}

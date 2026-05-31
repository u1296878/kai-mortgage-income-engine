import { apiRequest } from "./client";
import type { CaseResponse, CaseWithDocuments } from "../types/api";

export function listCases(): Promise<CaseResponse[]> {
  return apiRequest<CaseResponse[]>("/cases");
}

export function getCase(caseId: string): Promise<CaseResponse> {
  return apiRequest<CaseResponse>(`/cases/${caseId}`);
}

export function getCaseDocuments(caseId: string): Promise<CaseWithDocuments> {
  return apiRequest<CaseWithDocuments>(`/cases/${caseId}/documents`);
}

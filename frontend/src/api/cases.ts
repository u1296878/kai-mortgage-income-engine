import { apiRequest } from "./client";
import type { CaseResponse, CaseStatus, CaseWithDocuments } from "../types/api";

export function listCases(): Promise<CaseResponse[]> {
  return apiRequest<CaseResponse[]>("/cases");
}

export function getCase(caseId: string): Promise<CaseResponse> {
  return apiRequest<CaseResponse>(`/cases/${caseId}`);
}

export function getCaseDocuments(caseId: string): Promise<CaseWithDocuments> {
  return apiRequest<CaseWithDocuments>(`/cases/${caseId}/documents`);
}

export function createCase(title: string): Promise<CaseResponse> {
  return apiRequest<CaseResponse>("/cases", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function updateCaseStatus(caseId: string, status: CaseStatus): Promise<CaseResponse> {
  return apiRequest<CaseResponse>(`/cases/${caseId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function deleteCase(caseId: string): Promise<void> {
  return apiRequest<void>(`/cases/${caseId}`, { method: "DELETE" });
}

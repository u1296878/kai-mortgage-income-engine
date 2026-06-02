import { apiRequest } from "./client";
import type { DocumentResponse, DocumentType } from "../types/api";

export function uploadDocument(
  file: File,
  docType: DocumentType,
  caseId?: string,
): Promise<DocumentResponse> {
  const payload = new FormData();
  payload.append("file", file);
  payload.append("doc_type", docType);
  if (caseId) {
    payload.append("case_id", caseId);
  }
  return apiRequest<DocumentResponse>("/documents/upload", {
    method: "POST",
    body: payload,
  });
}

export function unlinkDocumentFromCase(documentId: string): Promise<DocumentResponse> {
  return apiRequest<DocumentResponse>(`/documents/${documentId}/case`, {
    method: "DELETE",
  });
}

export function deleteDocument(documentId: string): Promise<void> {
  return apiRequest<void>(`/documents/${documentId}`, { method: "DELETE" });
}

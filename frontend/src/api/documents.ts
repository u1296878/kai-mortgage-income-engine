import { apiRequest } from "./client";
import type { DocumentResponse, DocumentType } from "../types/api";

export function uploadDocument(
  file: File,
  docType: DocumentType,
): Promise<DocumentResponse> {
  const payload = new FormData();
  payload.append("file", file);
  payload.append("doc_type", docType);
  return apiRequest<DocumentResponse>("/documents/upload", {
    method: "POST",
    body: payload,
  });
}

export function linkDocumentToCase(
  documentId: string,
  caseId: string,
): Promise<DocumentResponse> {
  return apiRequest<DocumentResponse>(`/documents/${documentId}/case`, {
    method: "PATCH",
    body: JSON.stringify({ case_id: caseId }),
  });
}

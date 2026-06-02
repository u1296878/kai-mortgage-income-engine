export type UserRole = "broker" | "manager";

export type CaseStatus = "open" | "in_review" | "complete";

export type DocumentType =
  | "pay_stub"
  | "w2"
  | "tax_return"
  | "bank_statement"
  | "other";

export interface UserRead {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CaseResponse {
  id: string;
  broker_id: string;
  title: string;
  status: CaseStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentResponse {
  id: string;
  filename: string;
  doc_type: DocumentType;
  case_id: string | null;
  uploaded_at: string;
}

export interface CaseWithDocuments extends CaseResponse {
  documents: DocumentResponse[];
}

export interface JobStatusResponse {
  id: string;
  status: "pending" | "processing" | "complete" | "failed";
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ExtractedField {
  field: string;
  value: number;
  document_id: string;
  page: number;
  bounding_box: BoundingBox;
  raw_text?: string | null;
}

export interface ResultResponse {
  id: string;
  job_id: string;
  document_id: string;
  case_id: string | null;
  income_stream_id: string | null;
  doc_type: string;
  extracted_fields: ExtractedField[];
  annual_income: number | null;
  confidence: "low" | "medium" | "high" | null;
  notes: string | null;
  created_at: string;
}

export interface BorrowerResponse {
  id: string;
  case_id: string;
  broker_id: string;
  first_name: string;
  last_name: string;
  role: "primary" | "co_borrower";
  created_at: string;
  updated_at: string;
}

export interface IncomeStreamResponse {
  id: string;
  case_id: string;
  broker_id: string;
  borrower_id: string | null;
  name: string;
  stream_type: string;
  annual_income: number | null;
  confidence: "low" | "medium" | "high" | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseSummaryResponse {
  case_id: string;
  total_annual_income: number;
  borrowers: BorrowerResponse[];
  income_streams: IncomeStreamResponse[];
  results: ResultResponse[];
  sources: ExtractedField[];
}

export type SelfEmploymentKind =
  | "schedule_b"
  | "schedule_c"
  | "schedule_d"
  | "schedule_e_royalty"
  | "schedule_f"
  | "partnership"
  | "s_corporation"
  | "corporation";

export interface SelfEmploymentCalculationRequest {
  kind: SelfEmploymentKind;
  payload: Record<string, unknown>;
}

export interface SelfEmploymentCalculationCreate
  extends SelfEmploymentCalculationRequest {
  borrower_id?: string | null;
  label?: string | null;
}

export interface SelfEmploymentResultResponse {
  kind: SelfEmploymentKind;
  qualifying_monthly: number;
  annual_income: number;
  breakdown: Record<string, unknown>;
}

export interface SelfEmploymentCalculationResponse
  extends SelfEmploymentResultResponse {
  id: string;
  case_id: string;
  borrower_id: string | null;
  label: string | null;
  created_at: string;
}

export type NonTaxableKind = "income" | "social_security";

export type NonTaxableMethod = "gross_100" | "total_adjusted" | "current_monthly";

export type SocialSecurityMethod = "gross_100" | "adjusted";

export interface NonTaxableSourceInput {
  method: NonTaxableMethod;
  annual_gross?: number | null;
  annual_taxable?: number | null;
  current_monthly?: number | null;
  gross_up_rate: number;
}

export interface SocialSecuritySourceInput {
  method: SocialSecurityMethod;
  annual_gross?: number | null;
}

export interface NonTaxableCalculationRequest {
  kind: NonTaxableKind;
  income?: NonTaxableSourceInput | null;
  social_security?: SocialSecuritySourceInput | null;
}

export interface NonTaxableCalculationCreate extends NonTaxableCalculationRequest {
  borrower_id?: string | null;
  label?: string | null;
}

export interface NonTaxableResultResponse {
  monthly: number;
  method: string;
  taxable_monthly: number;
  eligible_monthly: number;
}

export interface NonTaxableCalculationResponse {
  id: string;
  case_id: string;
  borrower_id: string | null;
  label: string | null;
  kind: NonTaxableKind;
  monthly: number;
  annual_income: number;
  breakdown: NonTaxableResultResponse;
  created_at: string;
}

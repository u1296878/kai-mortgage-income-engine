export interface EmploymentPeriodInput {
  date_from: string;
  date_through: string;
  total_earnings: number;
  included: boolean;
}

export interface VariableBucketInput {
  periods: EmploymentPeriodInput[];
  annualize: boolean | null;
  use_ytd: boolean | null;
}

export interface BasePayInput {
  periods: EmploymentPeriodInput[];
  rate: number | null;
  pay_frequency: string | null;
  hours_weekly: number | null;
  rate_line_included: boolean;
}

export interface EmploymentIncomeInput {
  base_pay: BasePayInput;
  overtime: VariableBucketInput;
  bonus: VariableBucketInput;
  commission: VariableBucketInput;
  other: VariableBucketInput;
}

export interface PeriodResultResponse {
  months: number;
  monthly: number;
  pct_change: number | null;
}

export interface BucketResultResponse {
  qualifying_monthly: number;
  rate_of_pay_monthly: number;
  periods: PeriodResultResponse[];
}

export interface EmploymentResultResponse {
  base_pay: BucketResultResponse;
  overtime: BucketResultResponse;
  bonus: BucketResultResponse;
  commission: BucketResultResponse;
  other: BucketResultResponse;
  total_monthly: number;
}

export interface EmploymentCalculationCreate extends EmploymentIncomeInput {
  borrower_id?: string | null;
  label?: string | null;
}

export interface EmploymentCalculationResponse {
  id: string;
  case_id: string;
  borrower_id: string | null;
  label: string | null;
  total_monthly: number;
  annual_income: number;
  breakdown: EmploymentResultResponse;
  created_at: string;
}

export type RentalPropertyClass = "primary_2_4_unit" | "investment";

export type RentalMethod = "schedule_e" | "lease";

export interface ScheduleEYearInput {
  months_in_service: number;
  rents_received: number;
  total_expenses: number;
  insurance: number;
  mortgage_interest: number;
  taxes: number;
  depreciation_depletion: number;
  hoa_addback: number;
  casualty_one_time: number;
}

export interface RentalPropertyInput {
  property_class: RentalPropertyClass;
  method: RentalMethod;
  schedule_e_years: ScheduleEYearInput[];
  monthly_pitia?: number | null;
  gross_monthly_rent?: number | null;
  vacancy_factor: number;
}

export interface RentalCalculationCreate extends RentalPropertyInput {
  borrower_id?: string | null;
  label?: string | null;
  included?: boolean;
}

export interface RentalCalculationUpdate extends Partial<RentalPropertyInput> {
  borrower_id?: string | null;
  label?: string | null;
  included?: boolean;
}

export interface RentalYearResultResponse {
  months: number;
  annual_net: number;
  monthly_gross: number;
}

export interface RentalResultResponse {
  qualifying_monthly: number;
  property_class: string;
  method: string;
  years: RentalYearResultResponse[];
}

export interface RentalCalculationResponse {
  id: string;
  case_id: string;
  borrower_id: string | null;
  label: string | null;
  inputs: RentalPropertyInput;
  qualifying_monthly: number;
  annual_income: number;
  included: boolean;
  source_document_id: string | null;
  source_property_key: string | null;
  breakdown: RentalResultResponse;
  created_at: string;
}

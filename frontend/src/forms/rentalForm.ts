import type {
  RentalMethod,
  RentalPropertyClass,
  RentalPropertyInput,
  ScheduleEYearInput,
} from "../types/api";

// Schedule E line items beyond months_in_service (label shown next to each input).
export const YEAR_LINE_ITEMS: ReadonlyArray<[keyof ScheduleEYearForm, string]> = [
  ["rents_received", "Rents received"],
  ["total_expenses", "Total expenses"],
  ["insurance", "Insurance"],
  ["mortgage_interest", "Mortgage interest"],
  ["taxes", "Taxes"],
  ["depreciation_depletion", "Depreciation/depletion"],
  ["hoa_addback", "HOA add-back"],
  ["casualty_one_time", "Casualty (one-time)"],
];

export const YEAR_LABELS = ["Current year", "Prior year"] as const;

export interface ScheduleEYearForm {
  months_in_service: string;
  rents_received: string;
  total_expenses: string;
  insurance: string;
  mortgage_interest: string;
  taxes: string;
  depreciation_depletion: string;
  hoa_addback: string;
  casualty_one_time: string;
}

export interface RentalForm {
  property_class: RentalPropertyClass;
  method: RentalMethod;
  years: ScheduleEYearForm[];
  monthly_pitia: string;
  gross_monthly_rent: string;
  vacancy_factor: string;
}

function emptyYear(): ScheduleEYearForm {
  return {
    months_in_service: "",
    rents_received: "",
    total_expenses: "",
    insurance: "",
    mortgage_interest: "",
    taxes: "",
    depreciation_depletion: "",
    hoa_addback: "",
    casualty_one_time: "",
  };
}

export function initialRentalForm(): RentalForm {
  return {
    property_class: "primary_2_4_unit",
    method: "schedule_e",
    years: YEAR_LABELS.map(() => emptyYear()),
    monthly_pitia: "",
    gross_monthly_rent: "",
    vacancy_factor: "0.25",
  };
}

function isYearFilled(year: ScheduleEYearForm): boolean {
  return Object.values(year).some((value) => value !== "");
}

function toYear(year: ScheduleEYearForm): ScheduleEYearInput {
  return {
    months_in_service: year.months_in_service === "" ? 12 : Number(year.months_in_service),
    rents_received: Number(year.rents_received || 0),
    total_expenses: Number(year.total_expenses || 0),
    insurance: Number(year.insurance || 0),
    mortgage_interest: Number(year.mortgage_interest || 0),
    taxes: Number(year.taxes || 0),
    depreciation_depletion: Number(year.depreciation_depletion || 0),
    hoa_addback: Number(year.hoa_addback || 0),
    casualty_one_time: Number(year.casualty_one_time || 0),
  };
}

function optionalNumber(value: string): number | null {
  // Empty stays null so the backend's required-field guards can fire (422).
  return value === "" ? null : Number(value);
}

export function toRentalPayload(form: RentalForm): RentalPropertyInput {
  const isLease = form.method === "lease";
  const isInvestment = form.property_class === "investment";
  return {
    property_class: form.property_class,
    method: form.method,
    schedule_e_years: isLease ? [] : form.years.filter(isYearFilled).map(toYear),
    monthly_pitia: isInvestment ? optionalNumber(form.monthly_pitia) : null,
    gross_monthly_rent: isLease ? optionalNumber(form.gross_monthly_rent) : null,
    vacancy_factor: Number(form.vacancy_factor || 0.25),
  };
}

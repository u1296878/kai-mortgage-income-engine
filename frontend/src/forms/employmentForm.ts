import type {
  BasePayInput,
  EmploymentIncomeInput,
  EmploymentPeriodInput,
  VariableBucketInput,
} from "../types/api";

export type AyToggle = "Y" | "A";

// Periods are ordered YTD, prior, prior-prior (spec 2.5).
export const ROW_LABELS = ["YTD", "Prior year", "Prior-prior year"] as const;

// Dropdown options must match the backend PAY_FREQUENCY keys exactly (spec 1.2).
export const PAY_FREQUENCIES = [
  "hourly",
  "weekly",
  "biweekly",
  "semimonthly",
  "monthly",
  "quarterly",
  "semiannually",
  "annually",
  "varies",
] as const;

export interface PeriodForm {
  date_from: string;
  date_through: string;
  total_earnings: string;
  included: boolean;
}

export interface VariableBucketForm {
  periods: PeriodForm[];
  toggle: AyToggle;
}

export interface BasePayForm {
  periods: PeriodForm[];
  rate: string;
  pay_frequency: string;
  hours_weekly: string;
  rate_line_included: boolean;
}

export interface EmploymentForm {
  base_pay: BasePayForm;
  overtime: VariableBucketForm;
  bonus: VariableBucketForm;
  commission: VariableBucketForm;
  other: VariableBucketForm;
}

function emptyPeriods(): PeriodForm[] {
  return ROW_LABELS.map(() => ({
    date_from: "",
    date_through: "",
    total_earnings: "",
    included: true,
  }));
}

function emptyVariableBucket(): VariableBucketForm {
  return { periods: emptyPeriods(), toggle: "Y" };
}

export function initialEmploymentForm(): EmploymentForm {
  return {
    base_pay: {
      periods: emptyPeriods(),
      rate: "",
      pay_frequency: "hourly",
      hours_weekly: "",
      rate_line_included: false,
    },
    overtime: emptyVariableBucket(),
    bonus: emptyVariableBucket(),
    commission: emptyVariableBucket(),
    other: emptyVariableBucket(),
  };
}

function toPeriods(periods: PeriodForm[]): EmploymentPeriodInput[] {
  // Only rows with both dates filled are real worksheet periods.
  return periods
    .filter((period) => period.date_from !== "" && period.date_through !== "")
    .map((period) => ({
      date_from: period.date_from,
      date_through: period.date_through,
      total_earnings: Number(period.total_earnings || 0),
      included: period.included,
    }));
}

function toVariableBucket(bucket: VariableBucketForm): VariableBucketInput {
  return {
    periods: toPeriods(bucket.periods),
    annualize: bucket.toggle === "A",
    use_ytd: bucket.toggle === "Y",
  };
}

function toBasePay(base: BasePayForm): BasePayInput {
  const hourly = base.pay_frequency === "hourly";
  return {
    periods: toPeriods(base.periods),
    rate: base.rate_line_included ? Number(base.rate || 0) : null,
    pay_frequency: base.rate_line_included ? base.pay_frequency : null,
    hours_weekly:
      base.rate_line_included && hourly ? Number(base.hours_weekly || 0) : null,
    rate_line_included: base.rate_line_included,
  };
}

export function toEmploymentPayload(form: EmploymentForm): EmploymentIncomeInput {
  return {
    base_pay: toBasePay(form.base_pay),
    overtime: toVariableBucket(form.overtime),
    bonus: toVariableBucket(form.bonus),
    commission: toVariableBucket(form.commission),
    other: toVariableBucket(form.other),
  };
}

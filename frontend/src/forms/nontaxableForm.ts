import type {
  NonTaxableCalculationRequest,
  NonTaxableKind,
  NonTaxableMethod,
  SocialSecurityMethod,
} from "../types/nontaxable";

export interface NontaxableForm {
  kind: NonTaxableKind;
  incomeMethod: NonTaxableMethod;
  socialSecurityMethod: SocialSecurityMethod;
  annualGross: string;
  annualTaxable: string;
  currentMonthly: string;
  grossUpRate: string;
}

export const initialNontaxableForm: NontaxableForm = {
  kind: "income",
  incomeMethod: "gross_100",
  socialSecurityMethod: "gross_100",
  annualGross: "",
  annualTaxable: "",
  currentMonthly: "",
  grossUpRate: "0.25",
};

export function toNontaxablePayload(
  form: NontaxableForm,
): NonTaxableCalculationRequest {
  if (form.kind === "social_security") {
    return {
      kind: "social_security",
      social_security: {
        method: form.socialSecurityMethod,
        annual_gross: numberOrNull(form.annualGross),
      },
    };
  }
  return {
    kind: "income",
    income: {
      method: form.incomeMethod,
      annual_gross: numberOrNull(form.annualGross),
      annual_taxable: numberOrNull(form.annualTaxable),
      current_monthly: numberOrNull(form.currentMonthly),
      gross_up_rate: numberOrDefault(form.grossUpRate, 0.25),
    },
  };
}

function numberOrNull(value: string): number | null {
  if (value.trim() === "") {
    return null;
  }
  return Number(value);
}

function numberOrDefault(value: string, fallback: number): number {
  if (value.trim() === "") {
    return fallback;
  }
  return Number(value);
}

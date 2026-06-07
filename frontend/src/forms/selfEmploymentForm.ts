import type { SelfEmploymentCalculationRequest, SelfEmploymentKind } from "../types/selfEmployment";
import { configForKind, type ComponentConfig } from "./selfEmploymentConfig";

export interface SelfEmploymentYearForm {
  months: string;
  included: boolean;
  values: Record<string, string>;
}

export interface SelfEmploymentForm {
  kind: SelfEmploymentKind;
  components: Record<string, SelfEmploymentYearForm[]>;
}

export function initialSelfEmploymentForm(
  kind: SelfEmploymentKind = "schedule_c",
): SelfEmploymentForm {
  return {
    kind,
    components: Object.fromEntries(
      configForKind(kind).components.map((component) => [
        component.key,
        [emptyYear(component), emptyYear(component)],
      ]),
    ),
  };
}

export function changeSelfEmploymentKind(
  kind: SelfEmploymentKind,
): SelfEmploymentForm {
  return initialSelfEmploymentForm(kind);
}

export function updateSelfEmploymentYear(
  form: SelfEmploymentForm,
  componentKey: string,
  yearIndex: number,
  update: Partial<SelfEmploymentYearForm>,
): SelfEmploymentForm {
  const years = form.components[componentKey].map((year, index) =>
    index === yearIndex ? { ...year, ...update } : year,
  );
  return {
    ...form,
    components: { ...form.components, [componentKey]: years },
  };
}

export function updateSelfEmploymentValue(
  form: SelfEmploymentForm,
  componentKey: string,
  yearIndex: number,
  field: string,
  value: string,
): SelfEmploymentForm {
  const year = form.components[componentKey][yearIndex];
  return updateSelfEmploymentYear(form, componentKey, yearIndex, {
    values: { ...year.values, [field]: value },
  });
}

export function toSelfEmploymentPayload(
  form: SelfEmploymentForm,
): SelfEmploymentCalculationRequest {
  return {
    kind: form.kind,
    payload: Object.fromEntries(
      Object.entries(form.components).map(([componentKey, years]) => [
        componentKey,
        years.map((year) => ({
          months: numberFromText(year.months, 12),
          included: year.included,
          ...Object.fromEntries(
            Object.entries(year.values).map(([field, value]) => [
              field,
              numberFromText(value, 0),
            ]),
          ),
        })),
      ]),
    ),
  };
}

function emptyYear(component: ComponentConfig): SelfEmploymentYearForm {
  return {
    months: "12",
    included: true,
    values: Object.fromEntries(
      component.fields.map((field) => [
        field.name,
        field.name === "tax_year" ? "2025" : "",
      ]),
    ),
  };
}

function numberFromText(value: string, fallback: number): number {
  if (value.trim() === "") {
    return fallback;
  }
  return Number(value);
}

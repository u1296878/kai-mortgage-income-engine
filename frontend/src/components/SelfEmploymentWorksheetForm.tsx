import {
  SELF_EMPLOYMENT_KINDS,
  configForKind,
} from "../forms/selfEmploymentConfig";
import {
  changeSelfEmploymentKind,
  updateSelfEmploymentValue,
  updateSelfEmploymentYear,
  type SelfEmploymentForm,
} from "../forms/selfEmploymentForm";
import type { SelfEmploymentKind } from "../types/selfEmployment";

interface Props {
  form: SelfEmploymentForm;
  onChange: (form: SelfEmploymentForm) => void;
}

export function SelfEmploymentWorksheetForm({ form, onChange }: Props): JSX.Element {
  const config = configForKind(form.kind);

  return (
    <div className="space-y-5">
      <label className="block text-sm font-medium text-slate-700">
        Calculation kind
        <select
          aria-label="Self-employment kind"
          className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
          onChange={(event) =>
            onChange(changeSelfEmploymentKind(event.target.value as SelfEmploymentKind))
          }
          value={form.kind}
        >
          {SELF_EMPLOYMENT_KINDS.map((kind) => (
            <option key={kind.kind} value={kind.kind}>
              {kind.label}
            </option>
          ))}
        </select>
      </label>
      {config.components.map((component) => (
        <section
          className="space-y-3 border-t border-slate-200 pt-4"
          key={component.key}
        >
          <h2 className="text-sm font-semibold text-slate-900">{component.label}</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {form.components[component.key].map((year, yearIndex) => (
              <div
                className="space-y-3 rounded-md border border-slate-200 p-3"
                key={`${component.key}-${yearIndex}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-slate-800">
                    Year {yearIndex + 1}
                  </p>
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      aria-label={`${component.label} year ${yearIndex + 1} included`}
                      checked={year.included}
                      onChange={(event) =>
                        onChange(
                          updateSelfEmploymentYear(form, component.key, yearIndex, {
                            included: event.target.checked,
                          }),
                        )
                      }
                      type="checkbox"
                    />
                    Included
                  </label>
                </div>
                <NumberInput
                  label={`${component.label} year ${yearIndex + 1} Months`}
                  onChange={(value) =>
                    onChange(
                      updateSelfEmploymentYear(form, component.key, yearIndex, {
                        months: value,
                      }),
                    )
                  }
                  value={year.months}
                />
                {component.fields.map((field) => (
                  <NumberInput
                    key={field.name}
                    label={`${component.label} year ${yearIndex + 1} ${field.label}`}
                    onChange={(value) =>
                      onChange(
                        updateSelfEmploymentValue(
                          form,
                          component.key,
                          yearIndex,
                          field.name,
                          value,
                        ),
                      )
                    }
                    value={year.values[field.name] ?? ""}
                  />
                ))}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function NumberInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}): JSX.Element {
  return (
    <label className="block text-sm text-slate-700">
      {label}
      <input
        aria-label={label}
        className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
        onChange={(event) => onChange(event.target.value)}
        step="any"
        type="number"
        value={value}
      />
    </label>
  );
}

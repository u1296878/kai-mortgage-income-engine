import { RentalScheduleEYear } from "./RentalScheduleEYear";
import { YEAR_LABELS, type RentalForm } from "../forms/rentalForm";
import type { RentalMethod, RentalPropertyClass } from "../types/api";

interface Props {
  form: RentalForm;
  onChange: (form: RentalForm) => void;
}

const INPUT = "w-40 rounded-md border border-slate-300 px-2 py-1";
const SELECT = "rounded-md border border-slate-300 px-2 py-1";

export function RentalPropertyForm({ form, onChange }: Props): JSX.Element {
  const isLease = form.method === "lease";
  const isInvestment = form.property_class === "investment";

  return (
    <div className="space-y-4 text-sm">
      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2">
          Property class
          <select
            aria-label="Property class"
            className={SELECT}
            onChange={(event) =>
              onChange({ ...form, property_class: event.target.value as RentalPropertyClass })
            }
            value={form.property_class}
          >
            <option value="primary_2_4_unit">Primary residence (2-4 unit)</option>
            <option value="investment">Investment</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          Method
          <select
            aria-label="Method"
            className={SELECT}
            onChange={(event) =>
              onChange({ ...form, method: event.target.value as RentalMethod })
            }
            value={form.method}
          >
            <option value="schedule_e">Schedule E</option>
            <option value="lease">Lease</option>
          </select>
        </label>
      </div>
      {isInvestment ? (
        <label className="flex items-center gap-2">
          Monthly PITIA
          <input
            aria-label="Monthly PITIA"
            className={INPUT}
            onChange={(event) => onChange({ ...form, monthly_pitia: event.target.value })}
            type="number"
            value={form.monthly_pitia}
          />
        </label>
      ) : null}
      {isLease ? (
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2">
            Gross monthly rent
            <input
              aria-label="Gross monthly rent"
              className={INPUT}
              onChange={(event) => onChange({ ...form, gross_monthly_rent: event.target.value })}
              type="number"
              value={form.gross_monthly_rent}
            />
          </label>
          <label className="flex items-center gap-2">
            Vacancy factor
            <input
              aria-label="Vacancy factor"
              className={INPUT}
              onChange={(event) => onChange({ ...form, vacancy_factor: event.target.value })}
              type="number"
              value={form.vacancy_factor}
            />
          </label>
        </div>
      ) : (
        <div className="space-y-3">
          {form.years.map((year, index) => (
            <RentalScheduleEYear
              key={YEAR_LABELS[index]}
              legend={YEAR_LABELS[index]}
              onChange={(updated) =>
                onChange({
                  ...form,
                  years: form.years.map((current, i) => (i === index ? updated : current)),
                })
              }
              year={year}
            />
          ))}
        </div>
      )}
    </div>
  );
}

import { YEAR_LINE_ITEMS, type ScheduleEYearForm } from "../forms/rentalForm";

interface Props {
  legend: string;
  year: ScheduleEYearForm;
  onChange: (year: ScheduleEYearForm) => void;
}

export function RentalScheduleEYear({ legend, year, onChange }: Props): JSX.Element {
  function update(patch: Partial<ScheduleEYearForm>): void {
    onChange({ ...year, ...patch });
  }

  return (
    <fieldset className="space-y-2 border border-slate-200 p-3">
      <legend className="px-1 text-sm font-medium text-slate-700">{legend}</legend>
      <label className="flex items-center gap-2 text-sm">
        <span className="w-40 text-slate-600">Months in service</span>
        <input
          aria-label={`${legend} months in service`}
          className="w-32 rounded-md border border-slate-300 px-2 py-1"
          onChange={(event) => update({ months_in_service: event.target.value })}
          placeholder="12"
          type="number"
          value={year.months_in_service}
        />
      </label>
      {YEAR_LINE_ITEMS.map(([key, label]) => (
        <label className="flex items-center gap-2 text-sm" key={key}>
          <span className="w-40 text-slate-600">{label}</span>
          <input
            aria-label={`${legend} ${label}`}
            className="w-32 rounded-md border border-slate-300 px-2 py-1"
            onChange={(event) => update({ [key]: event.target.value })}
            type="number"
            value={year[key]}
          />
        </label>
      ))}
    </fieldset>
  );
}

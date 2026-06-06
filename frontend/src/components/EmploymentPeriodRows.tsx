import { ROW_LABELS, type PeriodForm } from "../forms/employmentForm";

interface Props {
  legend: string;
  periods: PeriodForm[];
  onChange: (periods: PeriodForm[]) => void;
}

export function EmploymentPeriodRows({ legend, periods, onChange }: Props): JSX.Element {
  function update(index: number, patch: Partial<PeriodForm>): void {
    onChange(periods.map((period, i) => (i === index ? { ...period, ...patch } : period)));
  }

  return (
    <fieldset className="space-y-2 border border-slate-200 p-3">
      <legend className="px-1 text-sm font-medium text-slate-700">{legend} periods</legend>
      {periods.map((period, index) => {
        const row = ROW_LABELS[index];
        return (
          <div key={row} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="w-28 text-slate-600">{row}</span>
            <input
              aria-label={`${legend} ${row} from`}
              className="rounded-md border border-slate-300 px-2 py-1"
              onChange={(event) => update(index, { date_from: event.target.value })}
              type="date"
              value={period.date_from}
            />
            <input
              aria-label={`${legend} ${row} through`}
              className="rounded-md border border-slate-300 px-2 py-1"
              onChange={(event) => update(index, { date_through: event.target.value })}
              type="date"
              value={period.date_through}
            />
            <input
              aria-label={`${legend} ${row} earnings`}
              className="w-32 rounded-md border border-slate-300 px-2 py-1"
              onChange={(event) => update(index, { total_earnings: event.target.value })}
              placeholder="Total earnings"
              type="number"
              value={period.total_earnings}
            />
            <label className="flex items-center gap-1">
              <input
                aria-label={`${legend} ${row} included`}
                checked={period.included}
                onChange={(event) => update(index, { included: event.target.checked })}
                type="checkbox"
              />
              Include
            </label>
          </div>
        );
      })}
    </fieldset>
  );
}

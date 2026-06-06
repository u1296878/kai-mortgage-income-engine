import { EmploymentPeriodRows } from "./EmploymentPeriodRows";
import type { AyToggle, VariableBucketForm } from "../forms/employmentForm";

interface Props {
  name: string;
  bucket: VariableBucketForm;
  onChange: (bucket: VariableBucketForm) => void;
}

export function EmploymentVariableBucket({ name, bucket, onChange }: Props): JSX.Element {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-900">{name}</h3>
      <EmploymentPeriodRows
        legend={name}
        onChange={(periods) => onChange({ ...bucket, periods })}
        periods={bucket.periods}
      />
      <label className="flex items-center gap-2 text-sm">
        YTD method
        <select
          aria-label={`${name} YTD method`}
          className="rounded-md border border-slate-300 px-2 py-1"
          onChange={(event) => onChange({ ...bucket, toggle: event.target.value as AyToggle })}
          value={bucket.toggle}
        >
          <option value="Y">Year-to-date (Y)</option>
          <option value="A">Annualize (A)</option>
        </select>
      </label>
    </section>
  );
}

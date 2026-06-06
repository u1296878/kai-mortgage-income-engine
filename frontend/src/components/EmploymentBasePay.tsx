import { EmploymentPeriodRows } from "./EmploymentPeriodRows";
import { PAY_FREQUENCIES, type BasePayForm } from "../forms/employmentForm";

interface Props {
  base: BasePayForm;
  onChange: (base: BasePayForm) => void;
}

export function EmploymentBasePay({ base, onChange }: Props): JSX.Element {
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-900">Base pay</h3>
      <EmploymentPeriodRows
        legend="Base pay"
        onChange={(periods) => onChange({ ...base, periods })}
        periods={base.periods}
      />
      <label className="flex items-center gap-2 text-sm">
        <input
          aria-label="Base pay rate line included"
          checked={base.rate_line_included}
          onChange={(event) => onChange({ ...base, rate_line_included: event.target.checked })}
          type="checkbox"
        />
        Include rate-of-pay line
      </label>
      {base.rate_line_included ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <input
            aria-label="Base pay rate"
            className="w-28 rounded-md border border-slate-300 px-2 py-1"
            onChange={(event) => onChange({ ...base, rate: event.target.value })}
            placeholder="Rate"
            type="number"
            value={base.rate}
          />
          <select
            aria-label="Base pay frequency"
            className="rounded-md border border-slate-300 px-2 py-1"
            onChange={(event) => onChange({ ...base, pay_frequency: event.target.value })}
            value={base.pay_frequency}
          >
            {PAY_FREQUENCIES.map((frequency) => (
              <option key={frequency} value={frequency}>
                {frequency}
              </option>
            ))}
          </select>
          {base.pay_frequency === "hourly" ? (
            <input
              aria-label="Base pay hours weekly"
              className="w-28 rounded-md border border-slate-300 px-2 py-1"
              onChange={(event) => onChange({ ...base, hours_weekly: event.target.value })}
              placeholder="Hours/week"
              type="number"
              value={base.hours_weekly}
            />
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

import { toCurrency } from "./formatters";
import type { BucketResultResponse, EmploymentResultResponse } from "../types/api";

const BUCKETS: ReadonlyArray<[string, keyof EmploymentResultResponse]> = [
  ["Base pay", "base_pay"],
  ["Overtime", "overtime"],
  ["Bonus", "bonus"],
  ["Commission", "commission"],
  ["Other", "other"],
];

interface Props {
  result: EmploymentResultResponse;
}

export function EmploymentResultView({ result }: Props): JSX.Element {
  return (
    <section className="space-y-3 rounded-md border border-slate-200 bg-white p-4">
      <h2 className="text-base font-semibold text-slate-900">Qualifying monthly income</h2>
      <p className="text-lg font-semibold text-slate-900">
        Total qualifying monthly income: {toCurrency(result.total_monthly)}
      </p>
      <div className="space-y-3">
        {BUCKETS.map(([label, key]) => (
          <BucketBreakdown bucket={result[key] as BucketResultResponse} key={key} label={label} />
        ))}
      </div>
    </section>
  );
}

function BucketBreakdown({
  label,
  bucket,
}: {
  label: string;
  bucket: BucketResultResponse;
}): JSX.Element {
  return (
    <div className="border-t border-slate-100 pt-2 text-sm">
      <p className="font-medium text-slate-800">
        {label}: {toCurrency(bucket.qualifying_monthly)}
        {bucket.rate_of_pay_monthly > 0
          ? ` (incl. rate-of-pay ${toCurrency(bucket.rate_of_pay_monthly)})`
          : null}
      </p>
      {bucket.periods.map((period, index) => (
        <p className="text-slate-600" key={index}>
          {period.months.toFixed(2)} mo · {toCurrency(period.monthly)}/mo
          {period.pct_change == null ? "" : ` · ${period.pct_change.toFixed(2)}% change`}
        </p>
      ))}
    </div>
  );
}

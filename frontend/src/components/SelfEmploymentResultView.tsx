import type { SelfEmploymentResultResponse } from "../types/selfEmployment";
import { toCurrency } from "./formatters";

interface Props {
  result: SelfEmploymentResultResponse;
}

export function SelfEmploymentResultView({ result }: Props): JSX.Element {
  return (
    <section className="space-y-3 rounded-md border border-slate-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-900">Calculation result</h2>
      <dl className="grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-slate-600">Kind</dt>
          <dd className="font-medium text-slate-900">{result.kind}</dd>
        </div>
        <div>
          <dt className="text-slate-600">Qualifying monthly</dt>
          <dd className="font-medium text-slate-900">
            {toCurrency(result.qualifying_monthly)}
          </dd>
        </div>
        <div>
          <dt className="text-slate-600">Annual income</dt>
          <dd className="font-medium text-slate-900">
            {toCurrency(result.annual_income)}
          </dd>
        </div>
      </dl>
    </section>
  );
}

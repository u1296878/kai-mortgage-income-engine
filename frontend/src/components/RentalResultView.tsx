import { toCurrency } from "./formatters";
import type { RentalResultResponse } from "../types/api";

interface Props {
  result: RentalResultResponse;
}

export function RentalResultView({ result }: Props): JSX.Element {
  return (
    <section className="space-y-3 rounded-md border border-slate-200 bg-white p-4">
      <h2 className="text-base font-semibold text-slate-900">Qualifying rental income</h2>
      <p className="text-lg font-semibold text-slate-900">
        Qualifying monthly income: {toCurrency(result.qualifying_monthly)}
      </p>
      <p className="text-sm text-slate-600">
        {result.property_class} · {result.method}
      </p>
      {result.years.map((year, index) => (
        <p className="border-t border-slate-100 pt-2 text-sm text-slate-600" key={index}>
          Year {index + 1}: {year.months.toFixed(2)} mo · net{" "}
          {toCurrency(year.annual_net)} · {toCurrency(year.monthly_gross)}/mo
        </p>
      ))}
    </section>
  );
}

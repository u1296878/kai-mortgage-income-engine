import type { NonTaxableResultResponse } from "../types/nontaxable";
import { toCurrency } from "./formatters";

interface Props {
  result: NonTaxableResultResponse;
}

export function NontaxableResultView({ result }: Props): JSX.Element {
  return (
    <section className="space-y-2 rounded-md border border-slate-200 p-4 text-sm">
      <p>
        <span className="font-medium">Qualifying monthly income:</span>{" "}
        {toCurrency(result.monthly)}
      </p>
      <p>
        <span className="font-medium">Taxable monthly:</span>{" "}
        {toCurrency(result.taxable_monthly)}
      </p>
      <p>
        <span className="font-medium">Eligible monthly:</span>{" "}
        {toCurrency(result.eligible_monthly)}
      </p>
    </section>
  );
}

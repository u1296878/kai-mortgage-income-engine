import type { CaseSummaryResponse } from "../types/api";
import { toCurrency } from "./formatters";

interface CaseSummaryPanelProps {
  summary: CaseSummaryResponse;
}

export function CaseSummaryPanel({ summary }: CaseSummaryPanelProps): JSX.Element {
  return (
    <div className="space-y-3 text-sm">
      <p>
        <span className="font-medium">Total annual income:</span> {toCurrency(summary.total_annual_income)}
      </p>
      <p>
        <span className="font-medium">Results:</span> {summary.results.length}
      </p>
      <p>
        <span className="font-medium">Income streams:</span> {summary.income_streams.length}
      </p>
      <p>
        <span className="font-medium">Employment calculations:</span>{" "}
        {summary.employment_calculations?.length ?? 0}
      </p>
      <p>
        <span className="font-medium">Rental calculations:</span>{" "}
        {summary.rental_calculations?.length ?? 0}
      </p>
      <p>
        <span className="font-medium">Borrowers:</span> {summary.borrowers.length}
      </p>
      <p>
        <span className="font-medium">Source references:</span> {summary.sources.length}
      </p>
    </div>
  );
}

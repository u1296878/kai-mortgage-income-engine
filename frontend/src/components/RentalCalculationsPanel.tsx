import { Link } from "react-router-dom";
import { toCurrency } from "./formatters";
import type { RentalCalculationResponse } from "../types/api";

interface Props {
  caseId: string;
  calculations: RentalCalculationResponse[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export function RentalCalculationsPanel({
  caseId,
  calculations,
  onDelete,
  deletingId,
}: Props): JSX.Element {
  return (
    <div className="space-y-3 text-sm">
      <Link className="text-blue-700 underline" to={`/income/rental?caseId=${caseId}`}>
        Add rental income
      </Link>
      {calculations.length === 0 ? (
        <p className="text-slate-600">No saved rental calculations.</p>
      ) : null}
      {calculations.map((calculation) => (
        <div
          className="flex items-center justify-between border-t border-slate-100 pt-2"
          key={calculation.id}
        >
          <div>
            <p className="font-medium text-slate-800">
              {calculation.label ?? "Rental income"}
            </p>
            <p className="text-slate-600">
              {toCurrency(calculation.qualifying_monthly)}/mo ·{" "}
              {toCurrency(calculation.annual_income)}/yr
            </p>
          </div>
          <button
            className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100"
            disabled={deletingId === calculation.id}
            onClick={() => onDelete(calculation.id)}
            type="button"
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}

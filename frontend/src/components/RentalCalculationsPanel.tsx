import { Link } from "react-router-dom";
import { toCurrency } from "./formatters";
import type { RentalCalculationResponse } from "../types/api";

interface Props {
  caseId: string;
  calculations: RentalCalculationResponse[];
  deletingId: string | null;
  onDelete: (id: string) => void;
  onIncludedChange: (id: string, included: boolean) => void;
  updatingId: string | null;
}

export function RentalCalculationsPanel({
  caseId,
  calculations,
  deletingId,
  onDelete,
  onIncludedChange,
  updatingId,
}: Props): JSX.Element {
  return (
    <div className="space-y-3 text-sm">
      {calculations.map((calculation) => (
        <div
          className="flex items-center justify-between border-t border-slate-100 pt-2 first:border-t-0 first:pt-0"
          key={calculation.id}
        >
          <div>
            <p className="font-medium text-slate-800">
              {calculation.label ?? "Rental income"}
            </p>
            <p className="text-slate-600">
              {toCurrency(calculation.qualifying_monthly)}/mo -{" "}
              {toCurrency(calculation.annual_income)}/yr
            </p>
            <label className="mt-1 flex items-center gap-2 text-slate-700">
              <input
                checked={calculation.included}
                disabled={updatingId === calculation.id}
                onChange={(event) => onIncludedChange(calculation.id, event.target.checked)}
                type="checkbox"
              />
              Included
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Link
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100"
              to={`/income/rental?caseId=${caseId}&calculationId=${calculation.id}`}
            >
              Edit
            </Link>
            <button
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100"
              disabled={deletingId === calculation.id}
              onClick={() => onDelete(calculation.id)}
              type="button"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

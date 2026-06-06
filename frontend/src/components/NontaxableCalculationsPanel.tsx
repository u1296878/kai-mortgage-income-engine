import { Link } from "react-router-dom";
import type { NonTaxableCalculationResponse } from "../types/nontaxable";
import { toCurrency } from "./formatters";

interface Props {
  caseId: string;
  calculations: NonTaxableCalculationResponse[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export function NontaxableCalculationsPanel({
  caseId,
  calculations,
  onDelete,
  deletingId,
}: Props): JSX.Element {
  return (
    <div className="space-y-3 text-sm">
      <Link className="text-blue-700 underline" to={`/income/nontaxable?caseId=${caseId}`}>
        Add non-taxable income
      </Link>
      {calculations.length === 0 ? (
        <p className="text-slate-600">No saved non-taxable calculations.</p>
      ) : null}
      {calculations.map((calculation) => (
        <div
          className="flex items-center justify-between border-t border-slate-100 pt-2"
          key={calculation.id}
        >
          <div>
            <p className="font-medium text-slate-800">
              {calculation.label ?? "Non-taxable income"}
            </p>
            <p className="text-slate-600">
              {calculation.kind === "social_security" ? "Social Security" : "Income"}{" "}
              {toCurrency(calculation.monthly)}/mo |{" "}
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

import { Link } from "react-router-dom";

interface IncomeWorksheetActionsProps {
  caseId: string;
}

const WORKSHEETS = [
  { label: "Employment", to: "/income/employment" },
  { label: "Rental", to: "/income/rental" },
  { label: "Non-taxable", to: "/income/nontaxable" },
  { label: "Self-employment", to: "/income/self-employment" },
];

export function IncomeWorksheetActions({ caseId }: IncomeWorksheetActionsProps): JSX.Element {
  return (
    <div className="grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
      {WORKSHEETS.map((worksheet) => (
        <Link
          className="rounded-md border border-slate-300 px-3 py-2 text-center font-medium text-slate-800 hover:bg-slate-50"
          key={worksheet.to}
          to={`${worksheet.to}?caseId=${caseId}`}
        >
          {worksheet.label}
        </Link>
      ))}
    </div>
  );
}

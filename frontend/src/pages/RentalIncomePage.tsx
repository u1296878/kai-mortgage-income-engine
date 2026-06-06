import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { calculateRentalIncome } from "../api/income";
import { RentalPropertyForm } from "../components/RentalPropertyForm";
import { RentalResultView } from "../components/RentalResultView";
import { RentalSaveToCase } from "../components/RentalSaveToCase";
import { initialRentalForm, toRentalPayload, type RentalForm } from "../forms/rentalForm";

export function RentalIncomePage(): JSX.Element {
  const [form, setForm] = useState<RentalForm>(initialRentalForm);
  const [searchParams] = useSearchParams();
  const caseId = searchParams.get("caseId");
  const mutation = useMutation({
    mutationFn: () => calculateRentalIncome(toRentalPayload(form)),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-900">Rental income worksheet</h1>
      {caseId ? <p className="text-sm text-slate-600">Saving to case {caseId}</p> : null}
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <RentalPropertyForm form={form} onChange={setForm} />
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Calculate
        </button>
      </form>
      {mutation.isError ? (
        <p className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Calculation failed: {(mutation.error as Error).message}
        </p>
      ) : null}
      {mutation.data ? <RentalResultView result={mutation.data} /> : null}
      {caseId ? <RentalSaveToCase caseId={caseId} form={form} /> : null}
    </div>
  );
}

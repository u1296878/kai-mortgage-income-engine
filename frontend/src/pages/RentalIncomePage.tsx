import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { calculateRentalIncome, getRentalCalculation } from "../api/income";
import { RentalPropertyForm } from "../components/RentalPropertyForm";
import { RentalResultView } from "../components/RentalResultView";
import { RentalSaveToCase } from "../components/RentalSaveToCase";
import {
  fromRentalPayload,
  initialRentalForm,
  toRentalPayload,
  type RentalForm,
} from "../forms/rentalForm";

export function RentalIncomePage(): JSX.Element {
  const [form, setForm] = useState<RentalForm>(initialRentalForm);
  const [searchParams] = useSearchParams();
  const caseId = searchParams.get("caseId");
  const calculationId = searchParams.get("calculationId");
  const calculationQuery = useQuery({
    queryKey: ["rentalCalculation", caseId, calculationId],
    queryFn: () => getRentalCalculation(caseId!, calculationId!),
    enabled: Boolean(caseId && calculationId),
  });
  const mutation = useMutation({
    mutationFn: () => calculateRentalIncome(toRentalPayload(form)),
  });
  useEffect(() => {
    if (calculationQuery.data) {
      setForm(fromRentalPayload(calculationQuery.data.inputs));
    }
  }, [calculationQuery.data]);

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-900">Rental income worksheet</h1>
      {caseId ? <p className="text-sm text-slate-600">Saving to case {caseId}</p> : null}
      {calculationQuery.isError ? (
        <p className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load rental calculation.
        </p>
      ) : null}
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
      {caseId ? (
        <RentalSaveToCase
          calculationId={calculationId}
          caseId={caseId}
          form={form}
          initialIncluded={calculationQuery.data?.included ?? true}
          initialLabel={calculationQuery.data?.label ?? null}
        />
      ) : null}
    </div>
  );
}

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { calculateNontaxableIncome } from "../api/income";
import { NontaxableResultView } from "../components/NontaxableResultView";
import { NontaxableSaveToCase } from "../components/NontaxableSaveToCase";
import { NontaxableSourceForm } from "../components/NontaxableSourceForm";
import {
  initialNontaxableForm,
  toNontaxablePayload,
  type NontaxableForm,
} from "../forms/nontaxableForm";

export function NontaxableIncomePage(): JSX.Element {
  const [form, setForm] = useState<NontaxableForm>(initialNontaxableForm);
  const [searchParams] = useSearchParams();
  const caseId = searchParams.get("caseId");
  const mutation = useMutation({
    mutationFn: () => calculateNontaxableIncome(toNontaxablePayload(form)),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-900">
        Non-taxable income worksheet
      </h1>
      {caseId ? <p className="text-sm text-slate-600">Saving to case {caseId}</p> : null}
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <NontaxableSourceForm form={form} onChange={setForm} />
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Calculate
        </button>
      </form>
      {mutation.isError ? (
        <p className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Calculation failed: {(mutation.error as Error).message}
        </p>
      ) : null}
      {mutation.data ? <NontaxableResultView result={mutation.data} /> : null}
      {caseId ? <NontaxableSaveToCase caseId={caseId} form={form} /> : null}
    </div>
  );
}

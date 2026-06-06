import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { calculateEmploymentIncome } from "../api/income";
import { EmploymentBasePay } from "../components/EmploymentBasePay";
import { EmploymentResultView } from "../components/EmploymentResultView";
import { EmploymentSaveToCase } from "../components/EmploymentSaveToCase";
import { EmploymentVariableBucket } from "../components/EmploymentVariableBucket";
import {
  initialEmploymentForm,
  toEmploymentPayload,
  type EmploymentForm,
} from "../forms/employmentForm";

export function EmploymentIncomePage(): JSX.Element {
  const [form, setForm] = useState<EmploymentForm>(initialEmploymentForm);
  const [searchParams] = useSearchParams();
  const caseId = searchParams.get("caseId");
  const mutation = useMutation({
    mutationFn: () => calculateEmploymentIncome(toEmploymentPayload(form)),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-900">Employment income worksheet</h1>
      {caseId ? (
        <p className="text-sm text-slate-600">Saving to case {caseId}</p>
      ) : null}
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <EmploymentBasePay
          base={form.base_pay}
          onChange={(base) => setForm((current) => ({ ...current, base_pay: base }))}
        />
        <EmploymentVariableBucket
          bucket={form.overtime}
          name="Overtime"
          onChange={(bucket) => setForm((current) => ({ ...current, overtime: bucket }))}
        />
        <EmploymentVariableBucket
          bucket={form.bonus}
          name="Bonus"
          onChange={(bucket) => setForm((current) => ({ ...current, bonus: bucket }))}
        />
        <EmploymentVariableBucket
          bucket={form.commission}
          name="Commission"
          onChange={(bucket) => setForm((current) => ({ ...current, commission: bucket }))}
        />
        <EmploymentVariableBucket
          bucket={form.other}
          name="Other"
          onChange={(bucket) => setForm((current) => ({ ...current, other: bucket }))}
        />
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white" type="submit">
          Calculate
        </button>
      </form>
      {mutation.isError ? (
        <p className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Calculation failed: {(mutation.error as Error).message}
        </p>
      ) : null}
      {mutation.data ? <EmploymentResultView result={mutation.data} /> : null}
      {caseId ? <EmploymentSaveToCase caseId={caseId} form={form} /> : null}
    </div>
  );
}

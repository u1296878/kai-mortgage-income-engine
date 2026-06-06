import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { saveEmploymentCalculation } from "../api/income";
import { toEmploymentPayload, type EmploymentForm } from "../forms/employmentForm";

interface Props {
  caseId: string;
  form: EmploymentForm;
}

export function EmploymentSaveToCase({ caseId, form }: Props): JSX.Element {
  const [label, setLabel] = useState("");
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: () =>
      saveEmploymentCalculation(caseId, {
        ...toEmploymentPayload(form),
        label: label.trim() || null,
      }),
    onSuccess: () => navigate(`/cases/${caseId}`),
  });

  return (
    <section className="space-y-2 rounded-md border border-slate-200 bg-slate-50 p-4">
      <h2 className="text-sm font-semibold text-slate-900">Save to case</h2>
      <div className="flex flex-wrap items-center gap-2">
        <input
          aria-label="Calculation label"
          className="min-w-56 rounded-md border border-slate-300 px-3 py-2 text-sm"
          onChange={(event) => setLabel(event.target.value)}
          placeholder="Label (e.g. employer name)"
          value={label}
        />
        <button
          className="rounded-md bg-blue-700 px-4 py-2 text-sm text-white"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate()}
          type="button"
        >
          Save to case
        </button>
      </div>
      {mutation.isError ? (
        <p className="text-sm text-red-700">
          Save failed: {(mutation.error as Error).message}
        </p>
      ) : null}
    </section>
  );
}

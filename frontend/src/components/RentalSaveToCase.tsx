import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { saveRentalCalculation, updateRentalCalculation } from "../api/income";
import { toRentalPayload, type RentalForm } from "../forms/rentalForm";

interface Props {
  caseId: string;
  calculationId?: string | null;
  form: RentalForm;
  initialIncluded?: boolean;
  initialLabel?: string | null;
}

export function RentalSaveToCase({
  caseId,
  calculationId,
  form,
  initialIncluded = true,
  initialLabel = null,
}: Props): JSX.Element {
  const [included, setIncluded] = useState(initialIncluded);
  const [label, setLabel] = useState(initialLabel ?? "");
  const navigate = useNavigate();
  useEffect(() => {
    setIncluded(initialIncluded);
    setLabel(initialLabel ?? "");
  }, [initialIncluded, initialLabel]);
  const mutation = useMutation({
    mutationFn: () => {
      const payload = {
        ...toRentalPayload(form),
        included,
        label: label.trim() || null,
      };
      return calculationId
        ? updateRentalCalculation(caseId, calculationId, payload)
        : saveRentalCalculation(caseId, payload);
    },
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
          placeholder="Label (e.g. property address)"
          value={label}
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            checked={included}
            onChange={(event) => setIncluded(event.target.checked)}
            type="checkbox"
          />
          Included
        </label>
        <button
          className="rounded-md bg-blue-700 px-4 py-2 text-sm text-white"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate()}
          type="button"
        >
          {calculationId ? "Update case" : "Save to case"}
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

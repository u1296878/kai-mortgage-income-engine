import type { CaseStatus } from "../types/api";

interface CaseStatusControlsProps {
  status: CaseStatus;
  updating: boolean;
  deleting: boolean;
  onStatusChange: (status: CaseStatus) => void;
  onDelete: () => void;
}

const NEXT_STATUS: Record<CaseStatus, CaseStatus | null> = {
  open: "in_review",
  in_review: "complete",
  complete: null,
};

export function CaseStatusControls({
  status,
  updating,
  deleting,
  onStatusChange,
  onDelete,
}: CaseStatusControlsProps): JSX.Element {
  const nextStatus = NEXT_STATUS[status];

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
      <span className="rounded-md border border-slate-300 px-2 py-1">Status: {status}</span>
      {nextStatus ? (
        <button
          className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100 disabled:opacity-50"
          disabled={updating}
          onClick={() => onStatusChange(nextStatus)}
          type="button"
        >
          Move to {nextStatus}
        </button>
      ) : (
        <span className="text-slate-500">Complete</span>
      )}
      <button
        className="rounded-md border border-red-300 px-3 py-1 text-red-700 hover:bg-red-50 disabled:opacity-50"
        disabled={deleting}
        onClick={onDelete}
        type="button"
      >
        Delete case
      </button>
    </div>
  );
}

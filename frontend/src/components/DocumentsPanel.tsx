import type { DocumentResponse, JobStatusResponse } from "../types/api";

interface DocumentsPanelProps {
  documents: DocumentResponse[];
  jobsByDocumentId: Record<string, JobStatusResponse | undefined>;
  busyDocumentId: string | null;
  onRemove: (documentId: string) => void;
  onDelete: (documentId: string) => void;
  onRetry: (jobId: string) => void;
}

export function DocumentsPanel({
  documents,
  jobsByDocumentId,
  busyDocumentId,
  onRemove,
  onDelete,
  onRetry,
}: DocumentsPanelProps): JSX.Element {
  if (documents.length === 0) {
    return <p className="text-sm text-slate-500">No documents linked to this case yet.</p>;
  }

  return (
    <ul className="space-y-2 text-sm">
      {documents.map((document) => {
        const job = jobsByDocumentId[document.id];
        return (
          <li key={document.id} className="rounded border border-slate-200 p-2">
            <p>{document.filename}</p>
            <p>Type: {document.doc_type}</p>
            <p>Job status: {job?.status ?? "unknown"}</p>
            {job?.error ? <p className="text-red-700">Error: {job.error}</p> : null}
            <div className="mt-2 flex flex-wrap gap-2">
              <button className="text-blue-700 underline" onClick={() => onRemove(document.id)} type="button">
                Remove from case
              </button>
              <button className="text-red-700 underline" onClick={() => onDelete(document.id)} type="button">
                Delete document
              </button>
              {job?.status === "failed" ? (
                <button
                  className="text-blue-700 underline disabled:opacity-50"
                  disabled={busyDocumentId === document.id}
                  onClick={() => onRetry(job.id)}
                  type="button"
                >
                  Retry
                </button>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

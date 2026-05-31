import type { ResultResponse } from "../types/api";
import { formatBoundingBox, toCurrency, toDate } from "./formatters";

interface ResultReviewProps {
  results: ResultResponse[];
}

export function ResultReview({ results }: ResultReviewProps): JSX.Element {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

  if (results.length === 0) {
    return <p className="text-sm text-slate-500">No extraction results yet.</p>;
  }

  return (
    <div className="space-y-4">
      {results.map((result) => (
        <article key={result.id} className="rounded-md border border-slate-200 bg-slate-25 p-3">
          <div className="mb-2 flex flex-wrap items-center gap-3 text-sm">
            <strong>{result.doc_type}</strong>
            <span>Annual Income: {toCurrency(result.annual_income)}</span>
            <span>Confidence: {result.confidence ?? "n/a"}</span>
            <span>Created: {toDate(result.created_at)}</span>
          </div>
          {result.notes ? <p className="mb-2 text-sm text-slate-700">{result.notes}</p> : null}
          <ul className="space-y-2">
            {result.extracted_fields.map((field, index) => {
              const sourceUrl = `${apiBaseUrl}/documents/${field.document_id}`;
              const value = field.raw_text ?? field.value.toString();
              return (
                <li key={`${field.field}-${index}`} className="rounded border border-slate-200 bg-white p-2 text-sm">
                  <p className="font-medium">{field.field}</p>
                  <p>Value: {value}</p>
                  <p>
                    Source: page {field.page} ({formatBoundingBox(field.bounding_box)})
                  </p>
                  <a className="text-blue-700 underline" href={sourceUrl} target="_blank" rel="noreferrer">
                    Open source document record
                  </a>
                </li>
              );
            })}
          </ul>
        </article>
      ))}
    </div>
  );
}

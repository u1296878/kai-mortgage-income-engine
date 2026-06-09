import { useState } from "react";
import type { FormEvent } from "react";
import type { DocumentType } from "../types/api";

const DOCUMENT_TYPES: DocumentType[] = ["w2", "pay_stub", "tax_return", "bank_statement", "other"];
const DOCUMENT_TYPE_HELP: Record<DocumentType, string> = {
  w2: "Extracts annual W-2 wage fields with source references.",
  pay_stub: "Extracts current-period and YTD pay fields for income review.",
  tax_return:
    "Extracts rental (Schedule E) and self-employment (Schedule C) income as reviewable drafts. AGI/total income are shown for reference only and are not added to the total.",
  bank_statement: "Extracts deposits and monthly deposit averages.",
  other: "Standalone rental-style extraction. For Schedule E rental review, prefer tax_return.",
};

interface DocumentUploadFormProps {
  onUpload: (file: File, docType: DocumentType) => Promise<unknown>;
  isSubmitting: boolean;
}

export function DocumentUploadForm({
  onUpload,
  isSubmitting,
}: DocumentUploadFormProps): JSX.Element {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<DocumentType>("w2");

  const submit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    if (!file) {
      return;
    }
    await onUpload(file, docType);
    setFile(null);
    event.currentTarget.reset();
  };

  return (
    <form className="space-y-3" onSubmit={submit}>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="doc-type">
          Document type
        </label>
        <select
          id="doc-type"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          defaultValue={docType}
          onChange={(event) => setDocType(event.target.value as DocumentType)}
        >
          {DOCUMENT_TYPES.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="document-file">
          PDF or image file
        </label>
        <input
          id="document-file"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          name="document-file"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          type="file"
          required
        />
      </div>
      <button
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        disabled={!file || isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Uploading..." : "Upload Document"}
      </button>
      <p className="text-xs text-slate-500">{DOCUMENT_TYPE_HELP[docType]}</p>
    </form>
  );
}

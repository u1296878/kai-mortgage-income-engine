import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { listCaseBorrowers } from "../api/borrowers";
import { getCase, getCaseDocuments } from "../api/cases";
import { uploadDocument } from "../api/documents";
import { listCaseIncomeStreams } from "../api/incomeStreams";
import { getDocumentJob, waitForJobCompletion } from "../api/jobs";
import { getJobResult, getCaseSummary } from "../api/results";
import { CaseSummaryPanel } from "../components/CaseSummaryPanel";
import { DocumentUploadForm } from "../components/DocumentUploadForm";
import { ResultReview } from "../components/ResultReview";
import { StateCard } from "../components/StateCard";
import type { DocumentType, ResultResponse } from "../types/api";

interface UploadState {
  stage: "idle" | "uploading" | "processing" | "done" | "error";
  message?: string;
  result?: ResultResponse;
}

export function CaseDetailPage(): JSX.Element {
  const { caseId } = useParams();
  const queryClient = useQueryClient();
  const [uploadState, setUploadState] = useState<UploadState>({ stage: "idle" });

  const caseQuery = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => getCase(caseId!),
    enabled: Boolean(caseId),
  });
  const documentsQuery = useQuery({
    queryKey: ["caseDocuments", caseId],
    queryFn: () => getCaseDocuments(caseId!),
    enabled: Boolean(caseId),
  });
  const summaryQuery = useQuery({
    queryKey: ["caseSummary", caseId],
    queryFn: () => getCaseSummary(caseId!),
    enabled: Boolean(caseId),
  });
  const streamsQuery = useQuery({
    queryKey: ["incomeStreams", caseId],
    queryFn: () => listCaseIncomeStreams(caseId!),
    enabled: Boolean(caseId),
  });
  const borrowersQuery = useQuery({
    queryKey: ["borrowers", caseId],
    queryFn: () => listCaseBorrowers(caseId!),
    enabled: Boolean(caseId),
  });

  const documents = documentsQuery.data?.documents ?? [];
  const jobQueries = useQueries({
    queries: documents.map((document) => ({
      queryKey: ["documentJob", document.id],
      queryFn: () => getDocumentJob(document.id),
      staleTime: 3000,
    })),
  });
  const jobByDocumentId = useMemo(() => {
    return documents.reduce<Record<string, string>>((acc, document, index) => {
      acc[document.id] = jobQueries[index]?.data?.status ?? "unknown";
      return acc;
    }, {});
  }, [documents, jobQueries]);

  const uploadMutation = useMutation({
    mutationFn: async ({ file, docType }: { file: File; docType: DocumentType }) => {
      setUploadState({ stage: "uploading", message: "Uploading document..." });
      const document = await uploadDocument(file, docType, caseId);
      setUploadState({ stage: "processing", message: "Waiting for extraction result..." });
      const job = await getDocumentJob(document.id);
      const finishedJob = await waitForJobCompletion(job.id);
      if (finishedJob.status !== "complete") {
        throw new Error(finishedJob.error ?? "Job failed");
      }
      return getJobResult(finishedJob.id);
    },
    onSuccess: (result) => {
      setUploadState({ stage: "done", message: "Extraction complete.", result });
      void queryClient.invalidateQueries({ queryKey: ["caseDocuments", caseId] });
      void queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] });
    },
    onError: (caught) => {
      const message = caught instanceof Error ? caught.message : "Upload failed";
      setUploadState({ stage: "error", message });
    },
  });

  if (!caseId) {
    return <p className="text-sm text-slate-600">Missing case identifier.</p>;
  }
  if (caseQuery.isLoading || documentsQuery.isLoading || summaryQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading case detail...</p>;
  }
  if (caseQuery.isError || documentsQuery.isError || summaryQuery.isError) {
    return <p className="text-sm text-red-700">Failed to load case detail.</p>;
  }

  return (
    <div className="space-y-4">
      <StateCard title="Case">
        <p className="text-sm font-medium">{caseQuery.data?.title}</p>
        <p className="text-sm text-slate-600">Case ID: {caseId}</p>
        <p className="text-sm text-slate-600">Status: {caseQuery.data?.status}</p>
      </StateCard>
      <StateCard title="Upload Document">
        <DocumentUploadForm
          isSubmitting={uploadMutation.isPending}
          onUpload={(file, docType) => uploadMutation.mutateAsync({ file, docType })}
        />
        {uploadState.stage !== "idle" ? <p className="mt-3 text-sm text-slate-700">{uploadState.message}</p> : null}
      </StateCard>
      <StateCard title="Documents and Jobs">
        {documents.length === 0 ? (
          <p className="text-sm text-slate-500">No documents linked to this case yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {documents.map((document) => (
              <li key={document.id} className="rounded border border-slate-200 p-2">
                <p>{document.filename}</p>
                <p>Type: {document.doc_type}</p>
                <p>Job status: {jobByDocumentId[document.id] ?? "unknown"}</p>
              </li>
            ))}
          </ul>
        )}
      </StateCard>
      <StateCard title="Case Summary">
        {summaryQuery.data ? <CaseSummaryPanel summary={summaryQuery.data} /> : null}
      </StateCard>
      <StateCard title="Extracted Results">
        <ResultReview results={summaryQuery.data?.results ?? []} />
        {uploadState.result ? <ResultReview results={[uploadState.result]} /> : null}
      </StateCard>
      <StateCard title="Income Streams and Borrowers">
        {streamsQuery.isLoading || borrowersQuery.isLoading ? (
          <p className="text-sm text-slate-500">Loading stream and borrower data...</p>
        ) : null}
        {streamsQuery.isError ? <p className="text-sm text-red-700">Failed to load income streams.</p> : null}
        {borrowersQuery.isError ? <p className="text-sm text-red-700">Failed to load borrowers.</p> : null}
        <p className="text-sm">Income streams: {streamsQuery.data?.length ?? 0}</p>
        <p className="text-sm">Borrowers: {borrowersQuery.data?.length ?? 0}</p>
      </StateCard>
    </div>
  );
}

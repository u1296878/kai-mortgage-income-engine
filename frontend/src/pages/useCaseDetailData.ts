import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { listCaseBorrowers } from "../api/borrowers";
import { deleteCase, getCase, getCaseDocuments, updateCaseStatus } from "../api/cases";
import { deleteDocument, unlinkDocumentFromCase, uploadDocument } from "../api/documents";
import {
  deleteEmploymentCalculation,
  deleteNontaxableCalculation,
  deleteRentalCalculation,
  deleteSelfEmploymentCalculation,
  updateRentalCalculation,
  updateSelfEmploymentCalculation,
} from "../api/income";
import { listCaseIncomeStreams } from "../api/incomeStreams";
import { getDocumentJob, retryJob, waitForJobCompletion } from "../api/jobs";
import { getCaseSummary, getJobResult } from "../api/results";
import type { CaseStatus, DocumentType, JobStatusResponse, ResultResponse } from "../types/api";

interface UploadState {
  stage: "idle" | "uploading" | "processing" | "done" | "error";
  message?: string;
  result?: ResultResponse;
}

const COMPLETE_JOB: JobStatusResponse = {
  id: "",
  status: "complete",
  error: null,
  created_at: "",
  started_at: null,
  completed_at: null,
};

export function useCaseDetailData(caseId: string | undefined, onCaseDeleted: () => void) {
  const queryClient = useQueryClient();
  const [uploadState, setUploadState] = useState<UploadState>({ stage: "idle" });
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null);

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
  const documentsWithResults = useMemo(() => {
    return new Set((summaryQuery.data?.results ?? []).map((result) => result.document_id));
  }, [summaryQuery.data?.results]);
  const documentsRequiringJobFetch = useMemo(() => {
    return documents.filter((document) => !documentsWithResults.has(document.id));
  }, [documents, documentsWithResults]);
  const jobQueries = useQueries({
    queries: documentsRequiringJobFetch.map((document) => ({
      queryKey: ["documentJob", document.id],
      queryFn: () => getDocumentJob(document.id),
      staleTime: 3000,
    })),
  });
  const jobByDocumentId = useMemo(() => {
    const byDocument = documents.reduce<Record<string, JobStatusResponse | undefined>>((acc, document) => {
      if (documentsWithResults.has(document.id)) {
        acc[document.id] = COMPLETE_JOB;
      }
      return acc;
    }, {});
    documentsRequiringJobFetch.forEach((document, index) => {
      byDocument[document.id] = jobQueries[index]?.data;
    });
    return byDocument;
  }, [documents, documentsWithResults, documentsRequiringJobFetch, jobQueries]);

  const refreshCaseData = (): void => {
    void queryClient.invalidateQueries({ queryKey: ["caseDocuments", caseId] });
    void queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] });
  };
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
      refreshCaseData();
    },
    onError: (caught) => {
      const message = caught instanceof Error ? caught.message : "Upload failed";
      setUploadState({ stage: "error", message });
    },
  });
  const statusMutation = useMutation({
    mutationFn: (status: CaseStatus) => updateCaseStatus(caseId!, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["case", caseId] }),
  });
  const deleteCaseMutation = useMutation({ mutationFn: () => deleteCase(caseId!), onSuccess: onCaseDeleted });
  const removeDocumentMutation = useMutation({ mutationFn: unlinkDocumentFromCase, onSuccess: refreshCaseData });
  const deleteDocumentMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: refreshCaseData,
    onSettled: () => setBusyDocumentId(null),
  });
  const retryMutation = useMutation({ mutationFn: retryJob, onSuccess: refreshCaseData });
  const deleteCalculationMutation = useMutation({
    mutationFn: (id: string) => deleteEmploymentCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
  const deleteRentalCalculationMutation = useMutation({
    mutationFn: (id: string) => deleteRentalCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
  const updateRentalCalculationMutation = useMutation({
    mutationFn: ({ id, included }: { id: string; included: boolean }) =>
      updateRentalCalculation(caseId!, id, { included }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
  const deleteNontaxableCalculationMutation = useMutation({
    mutationFn: (id: string) => deleteNontaxableCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
  const deleteSelfEmploymentCalculationMutation = useMutation({
    mutationFn: (id: string) => deleteSelfEmploymentCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
  const updateSelfEmploymentCalculationMutation = useMutation({
    mutationFn: ({ id, included }: { id: string; included: boolean }) =>
      updateSelfEmploymentCalculation(caseId!, id, { included }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });

  return {
    borrowersQuery,
    busyDocumentId,
    caseQuery,
    deleteCalculationMutation,
    deleteRentalCalculationMutation,
    updateRentalCalculationMutation,
    deleteNontaxableCalculationMutation,
    deleteSelfEmploymentCalculationMutation,
    updateSelfEmploymentCalculationMutation,
    deleteCaseMutation,
    deleteDocumentMutation,
    documents,
    documentsQuery,
    jobByDocumentId,
    removeDocumentMutation,
    retryMutation,
    setBusyDocumentId,
    statusMutation,
    streamsQuery,
    summaryQuery,
    uploadMutation,
    uploadState,
  };
}

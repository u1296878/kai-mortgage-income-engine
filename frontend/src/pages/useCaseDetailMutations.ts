import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { deleteCase, updateCaseStatus } from "../api/cases";
import { deleteDocument, unlinkDocumentFromCase, uploadDocument } from "../api/documents";
import {
  deleteEmploymentCalculation,
  deleteNontaxableCalculation,
  deleteRentalCalculation,
  deleteSelfEmploymentCalculation,
  updateRentalCalculation,
  updateSelfEmploymentCalculation,
} from "../api/income";
import { getDocumentJob, retryJob, waitForJobCompletion } from "../api/jobs";
import { getJobResult } from "../api/results";
import type { CaseStatus, DocumentType, ResultResponse } from "../types/api";


export interface UploadState {
  stage: "idle" | "uploading" | "processing" | "done" | "error";
  message?: string;
  result?: ResultResponse;
}


export function useCaseDetailMutations(
  caseId: string | undefined,
  onCaseDeleted: () => void,
) {
  const queryClient = useQueryClient();
  const [uploadState, setUploadState] = useState<UploadState>({ stage: "idle" });
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null);
  const refreshCaseData = (): void => {
    void queryClient.invalidateQueries({ queryKey: ["caseDocuments", caseId] });
    void queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] });
  };

  return {
    busyDocumentId,
    deleteCalculationMutation: useDeleteCalculation(caseId, queryClient),
    deleteCaseMutation: useMutation({ mutationFn: () => deleteCase(caseId!), onSuccess: onCaseDeleted }),
    deleteDocumentMutation: useMutation({
      mutationFn: deleteDocument,
      onSuccess: refreshCaseData,
      onSettled: () => setBusyDocumentId(null),
    }),
    deleteNontaxableCalculationMutation: useDeleteNontaxableCalculation(caseId, queryClient),
    deleteRentalCalculationMutation: useDeleteRentalCalculation(caseId, queryClient),
    deleteSelfEmploymentCalculationMutation: useDeleteSelfEmploymentCalculation(caseId, queryClient),
    removeDocumentMutation: useMutation({ mutationFn: unlinkDocumentFromCase, onSuccess: refreshCaseData }),
    retryMutation: useMutation({ mutationFn: retryJob, onSuccess: refreshCaseData }),
    setBusyDocumentId,
    statusMutation: useMutation({
      mutationFn: (status: CaseStatus) => updateCaseStatus(caseId!, status),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["case", caseId] }),
    }),
    updateRentalCalculationMutation: useUpdateRentalCalculation(caseId, queryClient),
    updateSelfEmploymentCalculationMutation: useUpdateSelfEmploymentCalculation(caseId, queryClient),
    uploadMutation: useMutation({
      mutationFn: (input: { file: File; docType: DocumentType }) => _upload(input, caseId, setUploadState),
      onSuccess: (result) => {
        setUploadState({ stage: "done", message: "Extraction complete.", result });
        refreshCaseData();
      },
      onError: (caught) => {
        const message = caught instanceof Error ? caught.message : "Upload failed";
        setUploadState({ stage: "error", message });
      },
    }),
    uploadState,
  };
}


async function _upload(
  { file, docType }: { file: File; docType: DocumentType },
  caseId: string | undefined,
  setUploadState: (state: UploadState) => void,
): Promise<ResultResponse> {
  setUploadState({ stage: "uploading", message: "Uploading document..." });
  const document = await uploadDocument(file, docType, caseId);
  setUploadState({ stage: "processing", message: "Waiting for extraction result..." });
  const job = await getDocumentJob(document.id);
  const finishedJob = await waitForJobCompletion(job.id);
  if (finishedJob.status !== "complete") {
    throw new Error(finishedJob.error ?? "Job failed");
  }
  return getJobResult(finishedJob.id);
}


function useDeleteCalculation(caseId: string | undefined, queryClient: QueryClient) {
  return useMutation({
    mutationFn: (id: string) => deleteEmploymentCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
}


function useDeleteRentalCalculation(caseId: string | undefined, queryClient: QueryClient) {
  return useMutation({
    mutationFn: (id: string) => deleteRentalCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
}


function useDeleteNontaxableCalculation(caseId: string | undefined, queryClient: QueryClient) {
  return useMutation({
    mutationFn: (id: string) => deleteNontaxableCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
}


function useDeleteSelfEmploymentCalculation(caseId: string | undefined, queryClient: QueryClient) {
  return useMutation({
    mutationFn: (id: string) => deleteSelfEmploymentCalculation(caseId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
}


function useUpdateRentalCalculation(caseId: string | undefined, queryClient: QueryClient) {
  return useMutation({
    mutationFn: ({ id, included }: { id: string; included: boolean }) =>
      updateRentalCalculation(caseId!, id, { included }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
}


function useUpdateSelfEmploymentCalculation(caseId: string | undefined, queryClient: QueryClient) {
  return useMutation({
    mutationFn: ({ id, included }: { id: string; included: boolean }) =>
      updateSelfEmploymentCalculation(caseId!, id, { included }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["caseSummary", caseId] }),
  });
}

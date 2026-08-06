import { useQueries, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { listCaseBorrowers } from "../api/borrowers";
import { getCase, getCaseDocuments } from "../api/cases";
import { listCaseIncomeStreams } from "../api/incomeStreams";
import { getDocumentJob } from "../api/jobs";
import { getCaseSummary } from "../api/results";
import type { JobStatusResponse } from "../types/api";
import { useCaseDetailMutations } from "./useCaseDetailMutations";

const COMPLETE_JOB: JobStatusResponse = {
  id: "",
  status: "complete",
  error: null,
  created_at: "",
  started_at: null,
  completed_at: null,
};

export function useCaseDetailData(caseId: string | undefined, onCaseDeleted: () => void) {
  const mutations = useCaseDetailMutations(caseId, onCaseDeleted);

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

  return {
    borrowersQuery,
    busyDocumentId: mutations.busyDocumentId,
    caseQuery,
    deleteCalculationMutation: mutations.deleteCalculationMutation,
    deleteRentalCalculationMutation: mutations.deleteRentalCalculationMutation,
    updateRentalCalculationMutation: mutations.updateRentalCalculationMutation,
    deleteNontaxableCalculationMutation: mutations.deleteNontaxableCalculationMutation,
    deleteSelfEmploymentCalculationMutation: mutations.deleteSelfEmploymentCalculationMutation,
    updateSelfEmploymentCalculationMutation: mutations.updateSelfEmploymentCalculationMutation,
    deleteCaseMutation: mutations.deleteCaseMutation,
    deleteDocumentMutation: mutations.deleteDocumentMutation,
    documents,
    documentsQuery,
    jobByDocumentId,
    removeDocumentMutation: mutations.removeDocumentMutation,
    retryMutation: mutations.retryMutation,
    setBusyDocumentId: mutations.setBusyDocumentId,
    statusMutation: mutations.statusMutation,
    streamsQuery,
    summaryQuery,
    uploadMutation: mutations.uploadMutation,
    uploadState: mutations.uploadState,
  };
}

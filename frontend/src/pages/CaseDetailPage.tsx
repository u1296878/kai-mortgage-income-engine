import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CaseSummaryPanel } from "../components/CaseSummaryPanel";
import { CaseStatusControls } from "../components/CaseStatusControls";
import { EmploymentCalculationsPanel } from "../components/EmploymentCalculationsPanel";
import { IncomeWorksheetActions } from "../components/IncomeWorksheetActions";
import { NontaxableCalculationsPanel } from "../components/NontaxableCalculationsPanel";
import { RentalCalculationsPanel } from "../components/RentalCalculationsPanel";
import { SelfEmploymentCalculationsPanel } from "../components/SelfEmploymentCalculationsPanel";
import { DocumentUploadForm } from "../components/DocumentUploadForm";
import { DocumentViewer } from "../components/DocumentViewer";
import { DocumentsPanel } from "../components/DocumentsPanel";
import { ResultReview } from "../components/ResultReview";
import { StateCard } from "../components/StateCard";
import type { ExtractedField } from "../types/api";
import { useCaseDetailData } from "./useCaseDetailData";

export function CaseDetailPage(): JSX.Element {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [selectedSource, setSelectedSource] = useState<ExtractedField | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const data = useCaseDetailData(caseId, () => navigate("/cases"));

  if (!caseId) {
    return <p className="text-sm text-slate-600">Missing case identifier.</p>;
  }
  if (data.caseQuery.isLoading || data.documentsQuery.isLoading || data.summaryQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading case detail...</p>;
  }
  if (data.caseQuery.isError || data.documentsQuery.isError || data.summaryQuery.isError) {
    return <p className="text-sm text-red-700">Failed to load case detail.</p>;
  }

  const openSourceViewer = (field: ExtractedField): void => {
    setSelectedSource(field);
    setViewerOpen(true);
  };
  const closeSourceViewer = (): void => {
    setViewerOpen(false);
    setSelectedSource(null);
  };
  const summary = data.summaryQuery.data;
  const employmentCalculations = summary?.employment_calculations ?? [];
  const rentalCalculations = summary?.rental_calculations ?? [];
  const nontaxableCalculations = summary?.nontaxable_calculations ?? [];
  const selfEmploymentCalculations = summary?.self_employment_calculations ?? [];
  const employmentDeletingId = data.deleteCalculationMutation.isPending ? (data.deleteCalculationMutation.variables ?? null) : null;
  const rentalDeletingId = data.deleteRentalCalculationMutation.isPending ? (data.deleteRentalCalculationMutation.variables ?? null) : null;
  const rentalUpdatingId = data.updateRentalCalculationMutation.isPending ? (data.updateRentalCalculationMutation.variables?.id ?? null) : null;
  const nontaxableDeletingId = data.deleteNontaxableCalculationMutation.isPending ? (data.deleteNontaxableCalculationMutation.variables ?? null) : null;
  const selfEmploymentDeletingId = data.deleteSelfEmploymentCalculationMutation.isPending ? (data.deleteSelfEmploymentCalculationMutation.variables ?? null) : null;

  return (
    <div className="space-y-4">
      <StateCard title="Case">
        <p className="text-sm font-medium">{data.caseQuery.data?.title}</p>
        <p className="text-sm text-slate-600">Case ID: {caseId}</p>
        {data.caseQuery.data ? (
          <CaseStatusControls
            deleting={data.deleteCaseMutation.isPending}
            onDelete={() => {
              if (window.confirm("Are you sure? This will delete all documents and results.")) {
                data.deleteCaseMutation.mutate();
              }
            }}
            onStatusChange={(status) => data.statusMutation.mutate(status)}
            status={data.caseQuery.data.status}
            updating={data.statusMutation.isPending}
          />
        ) : null}
      </StateCard>
      <StateCard title="Upload Document">
        <DocumentUploadForm
          isSubmitting={data.uploadMutation.isPending}
          onUpload={(file, docType) => data.uploadMutation.mutateAsync({ file, docType })}
        />
        {data.uploadState.stage !== "idle" ? <p className="mt-3 text-sm text-slate-700">{data.uploadState.message}</p> : null}
      </StateCard>
      <StateCard title="Documents and Jobs">
        <DocumentsPanel
          busyDocumentId={data.busyDocumentId}
          documents={data.documents}
          jobsByDocumentId={data.jobByDocumentId}
          onDelete={(documentId) => {
            if (window.confirm("Are you sure? This will delete the document and result.")) {
              data.setBusyDocumentId(documentId);
              data.deleteDocumentMutation.mutate(documentId);
            }
          }}
          onRemove={(documentId) => data.removeDocumentMutation.mutate(documentId)}
          onRetry={(jobId) => data.retryMutation.mutate(jobId)}
        />
      </StateCard>
      <StateCard title="Case Summary">
        {summary ? <CaseSummaryPanel summary={summary} /> : null}
      </StateCard>
      <StateCard title="Income Worksheets">
        <IncomeWorksheetActions caseId={caseId} />
      </StateCard>
      {employmentCalculations.length > 0 ? (
        <StateCard title="Employment Income">
          <EmploymentCalculationsPanel
            calculations={employmentCalculations}
            deletingId={employmentDeletingId}
            onDelete={(calculationId) => data.deleteCalculationMutation.mutate(calculationId)}
          />
        </StateCard>
      ) : null}
      {rentalCalculations.length > 0 ? (
        <StateCard title="Rental Income">
          <RentalCalculationsPanel
            caseId={caseId}
            calculations={rentalCalculations}
            deletingId={rentalDeletingId}
            onDelete={(calculationId) => data.deleteRentalCalculationMutation.mutate(calculationId)}
            onIncludedChange={(calculationId, included) => {
              data.updateRentalCalculationMutation.mutate({ id: calculationId, included });
            }}
            updatingId={rentalUpdatingId}
          />
        </StateCard>
      ) : null}
      {nontaxableCalculations.length > 0 ? (
        <StateCard title="Non-taxable Income">
          <NontaxableCalculationsPanel
            calculations={nontaxableCalculations}
            deletingId={nontaxableDeletingId}
            onDelete={(calculationId) => {
              data.deleteNontaxableCalculationMutation.mutate(calculationId);
            }}
          />
        </StateCard>
      ) : null}
      {selfEmploymentCalculations.length > 0 ? (
        <StateCard title="Self-employment Income">
          <SelfEmploymentCalculationsPanel
            calculations={selfEmploymentCalculations}
            deletingId={selfEmploymentDeletingId}
            onDelete={(calculationId) => {
              data.deleteSelfEmploymentCalculationMutation.mutate(calculationId);
            }}
          />
        </StateCard>
      ) : null}
      <StateCard title="Extracted Results">
        <ResultReview results={summary?.results ?? []} onViewSource={openSourceViewer} />
        {data.uploadState.result ? <ResultReview results={[data.uploadState.result]} onViewSource={openSourceViewer} /> : null}
      </StateCard>
      <StateCard title="Income Streams and Borrowers">
        {data.streamsQuery.isLoading || data.borrowersQuery.isLoading ? (
          <p className="text-sm text-slate-500">Loading stream and borrower data...</p>
        ) : null}
        {data.streamsQuery.isError ? <p className="text-sm text-red-700">Failed to load income streams.</p> : null}
        {data.borrowersQuery.isError ? <p className="text-sm text-red-700">Failed to load borrowers.</p> : null}
        <p className="text-sm">Income streams: {data.streamsQuery.data?.length ?? 0}</p>
        <p className="text-sm">Borrowers: {data.borrowersQuery.data?.length ?? 0}</p>
      </StateCard>
      <DocumentViewer
        isOpen={viewerOpen}
        documentId={selectedSource?.document_id ?? null}
        onClose={closeSourceViewer}
        source={selectedSource}
      />
    </div>
  );
}

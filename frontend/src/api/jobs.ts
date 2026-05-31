import { apiRequest } from "./client";
import type { JobStatusResponse } from "../types/api";

const TERMINAL_STATUSES = new Set(["complete", "failed"]);

export function getDocumentJob(documentId: string): Promise<JobStatusResponse> {
  return apiRequest<JobStatusResponse>(`/documents/${documentId}/job`);
}

export function getJob(jobId: string): Promise<JobStatusResponse> {
  return apiRequest<JobStatusResponse>(`/jobs/${jobId}`);
}

export async function waitForJobCompletion(
  jobId: string,
  timeoutMs = 120000,
): Promise<JobStatusResponse> {
  const startedAt = Date.now();
  let job = await getJob(jobId);

  while (!TERMINAL_STATUSES.has(job.status)) {
    if (Date.now() - startedAt > timeoutMs) {
      throw new Error("Job processing timed out");
    }
    await sleep(2000);
    job = await getJob(jobId);
  }

  return job;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

import { apiRequest } from "./client";
import type {
  SelfEmploymentCalculationCreate,
  SelfEmploymentCalculationRequest,
  SelfEmploymentCalculationResponse,
  SelfEmploymentCalculationUpdate,
  SelfEmploymentResultResponse,
} from "../types/selfEmployment";


export function calculateSelfEmployment(
  input: SelfEmploymentCalculationRequest,
): Promise<SelfEmploymentResultResponse> {
  return apiRequest<SelfEmploymentResultResponse>("/income/self-employment/calculate", {
    method: "POST",
    body: JSON.stringify(input),
  });
}


export function saveSelfEmploymentCalculation(
  caseId: string,
  payload: SelfEmploymentCalculationCreate,
): Promise<SelfEmploymentCalculationResponse> {
  return apiRequest<SelfEmploymentCalculationResponse>(
    `/cases/${caseId}/self-employment-calculations`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}


export function listSelfEmploymentCalculations(
  caseId: string,
): Promise<SelfEmploymentCalculationResponse[]> {
  return apiRequest<SelfEmploymentCalculationResponse[]>(
    `/cases/${caseId}/self-employment-calculations`,
  );
}


export function deleteSelfEmploymentCalculation(
  caseId: string,
  id: string,
): Promise<void> {
  return apiRequest<void>(`/cases/${caseId}/self-employment-calculations/${id}`, {
    method: "DELETE",
  });
}


export function updateSelfEmploymentCalculation(
  caseId: string,
  id: string,
  payload: SelfEmploymentCalculationUpdate,
): Promise<SelfEmploymentCalculationResponse> {
  return apiRequest<SelfEmploymentCalculationResponse>(
    `/cases/${caseId}/self-employment-calculations/${id}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

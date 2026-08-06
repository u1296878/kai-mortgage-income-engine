import { apiRequest } from "./client";
import type {
  NonTaxableCalculationCreate,
  NonTaxableCalculationRequest,
  NonTaxableCalculationResponse,
  NonTaxableResultResponse,
} from "../types/nontaxable";


export function calculateNontaxableIncome(
  input: NonTaxableCalculationRequest,
): Promise<NonTaxableResultResponse> {
  return apiRequest<NonTaxableResultResponse>("/income/nontaxable/calculate", {
    method: "POST",
    body: JSON.stringify(input),
  });
}


export function saveNontaxableCalculation(
  caseId: string,
  payload: NonTaxableCalculationCreate,
): Promise<NonTaxableCalculationResponse> {
  return apiRequest<NonTaxableCalculationResponse>(
    `/cases/${caseId}/nontaxable-calculations`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}


export function listNontaxableCalculations(
  caseId: string,
): Promise<NonTaxableCalculationResponse[]> {
  return apiRequest<NonTaxableCalculationResponse[]>(
    `/cases/${caseId}/nontaxable-calculations`,
  );
}


export function deleteNontaxableCalculation(caseId: string, id: string): Promise<void> {
  return apiRequest<void>(`/cases/${caseId}/nontaxable-calculations/${id}`, {
    method: "DELETE",
  });
}

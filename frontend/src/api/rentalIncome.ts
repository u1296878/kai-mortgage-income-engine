import { apiRequest } from "./client";
import type {
  RentalCalculationCreate,
  RentalCalculationResponse,
  RentalCalculationUpdate,
  RentalPropertyInput,
  RentalResultResponse,
} from "../types/api";


export function calculateRentalIncome(
  input: RentalPropertyInput,
): Promise<RentalResultResponse> {
  return apiRequest<RentalResultResponse>("/income/rental/calculate", {
    method: "POST",
    body: JSON.stringify(input),
  });
}


export function saveRentalCalculation(
  caseId: string,
  payload: RentalCalculationCreate,
): Promise<RentalCalculationResponse> {
  return apiRequest<RentalCalculationResponse>(
    `/cases/${caseId}/rental-calculations`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}


export function listRentalCalculations(
  caseId: string,
): Promise<RentalCalculationResponse[]> {
  return apiRequest<RentalCalculationResponse[]>(
    `/cases/${caseId}/rental-calculations`,
  );
}


export function getRentalCalculation(
  caseId: string,
  id: string,
): Promise<RentalCalculationResponse> {
  return apiRequest<RentalCalculationResponse>(
    `/cases/${caseId}/rental-calculations/${id}`,
  );
}


export function updateRentalCalculation(
  caseId: string,
  id: string,
  payload: RentalCalculationUpdate,
): Promise<RentalCalculationResponse> {
  return apiRequest<RentalCalculationResponse>(
    `/cases/${caseId}/rental-calculations/${id}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}


export function deleteRentalCalculation(caseId: string, id: string): Promise<void> {
  return apiRequest<void>(`/cases/${caseId}/rental-calculations/${id}`, {
    method: "DELETE",
  });
}

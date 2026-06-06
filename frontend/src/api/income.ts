import { apiRequest } from "./client";
import type {
  EmploymentCalculationCreate,
  EmploymentCalculationResponse,
  EmploymentIncomeInput,
  EmploymentResultResponse,
  RentalCalculationCreate,
  RentalCalculationResponse,
  RentalPropertyInput,
  RentalResultResponse,
} from "../types/api";

export function calculateEmploymentIncome(
  input: EmploymentIncomeInput,
): Promise<EmploymentResultResponse> {
  return apiRequest<EmploymentResultResponse>("/income/employment/calculate", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function saveEmploymentCalculation(
  caseId: string,
  payload: EmploymentCalculationCreate,
): Promise<EmploymentCalculationResponse> {
  return apiRequest<EmploymentCalculationResponse>(
    `/cases/${caseId}/employment-calculations`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function listEmploymentCalculations(
  caseId: string,
): Promise<EmploymentCalculationResponse[]> {
  return apiRequest<EmploymentCalculationResponse[]>(
    `/cases/${caseId}/employment-calculations`,
  );
}

export function deleteEmploymentCalculation(caseId: string, id: string): Promise<void> {
  return apiRequest<void>(`/cases/${caseId}/employment-calculations/${id}`, {
    method: "DELETE",
  });
}

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

export function deleteRentalCalculation(caseId: string, id: string): Promise<void> {
  return apiRequest<void>(`/cases/${caseId}/rental-calculations/${id}`, {
    method: "DELETE",
  });
}

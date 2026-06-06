import { apiRequest } from "./client";
import type {
  EmploymentCalculationCreate,
  EmploymentCalculationResponse,
  EmploymentIncomeInput,
  EmploymentResultResponse,
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

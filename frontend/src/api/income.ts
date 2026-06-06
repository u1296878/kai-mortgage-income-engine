import { apiRequest } from "./client";
import type {
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

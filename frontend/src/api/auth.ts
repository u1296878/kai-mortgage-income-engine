import { apiRequest } from "./client";
import type { TokenResponse, UserRead } from "../types/api";

export interface LoginPayload {
  email: string;
  password: string;
}

export function login(payload: LoginPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchMe(): Promise<UserRead> {
  return apiRequest<UserRead>("/auth/me");
}

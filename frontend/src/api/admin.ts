import { apiRequest } from "./client";
import type { UserRead } from "../types/api";

export function listBrokers(): Promise<UserRead[]> {
  return apiRequest<UserRead[]>("/admin/brokers");
}

export function updateBrokerStatus(brokerId: string, isActive: boolean): Promise<UserRead> {
  return apiRequest<UserRead>(`/admin/brokers/${brokerId}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

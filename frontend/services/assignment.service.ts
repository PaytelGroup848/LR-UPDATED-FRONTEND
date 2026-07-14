import type { ApiResult, Id } from "@/types/admin";
import { deleteJson, postJson } from "./api";

export function assignApplication(appId: Id, userId: Id) {
  return postJson<ApiResult>(`/api/apps/${appId}/assign`, { user_id: userId });
}

export function unassignApplication(appId: Id, userId: Id) {
  return deleteJson<ApiResult>(`/api/apps/${appId}/assign/${userId}`);
}

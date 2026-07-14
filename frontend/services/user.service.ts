import type { ApiResult, Id, User } from "@/types/admin";
import { apiFetch, deleteJson, getJson, postForm, postJson } from "./api";

export function getUsers() {
  return apiFetch<{ users?: User[] } | User[]>("/users")
    .then((data) => (Array.isArray(data) ? data : data.users || []))
    .catch(() => []);
}

export function createUser(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/users", payload);
}

export function updateUser(id: Id, payload: Record<string, unknown>) {
  return postJson<ApiResult>(`/users/${id}`, payload);
}

export function deleteUser(id: Id) {
  return deleteJson<ApiResult>(`/users/${id}`);
}

export function bulkDeleteUsers(user_ids: Id[]) {
  return postJson<ApiResult>("/users/bulk-delete", { user_ids });
}

export function importUsersCsv(formData: FormData) {
  return postForm<ApiResult>("/users/import-csv", formData);
}

export function loadUserAssignments(userId: Id) {
  return apiFetch(`/api/apps/assignments/user/${userId}`);
}

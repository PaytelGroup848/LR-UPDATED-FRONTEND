import type { ApiResult, Application, Id, Server } from "@/types/admin";
import { apiFetch, deleteJson, getJson, postForm, postJson } from "./api";

export function getServers() {
  return apiFetch<{ servers?: Server[] } | Server[]>("/portal/api/servers")
    .then((data) => (Array.isArray(data) ? data : data.servers || []))
    .catch(() => []);
}

export function createServer(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/add-server", payload);
}

export function testRdp(id: Id) {
  return postJson<ApiResult>(`/servers/${id}/rdp-test`, {});
}

export function getApplications() {
  return apiFetch<{ apps?: Application[] } | Application[]>("/api/apps")
    .then((data) => (Array.isArray(data) ? data : data.apps || []))
    .catch(() => []);
}

export function createApplication(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/api/apps", payload);
}

export function updateApplication(id: Id, payload: Record<string, unknown>) {
  return postJson<ApiResult>(`/api/apps/${id}`, payload);
}

export function deleteApplication(id: Id) {
  return deleteJson<ApiResult>(`/api/apps/${id}`);
}

export function uploadApplication(formData: FormData) {
  return postForm<ApiResult>("/api/apps/upload", formData);
}

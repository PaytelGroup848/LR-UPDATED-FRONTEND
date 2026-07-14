import type { Agent, ApiResult, Monitoring, Transfer } from "@/types/admin";
import { apiFetch, getJson, postForm, postJson } from "./api";

export function getAgents() {
  return apiFetch<{ agents?: Agent[]; items?: Agent[] } | Agent[]>("/agents")
    .then((data) => (Array.isArray(data) ? data : data.agents || data.items || []))
    .catch(() => []);
}

export function getMonitoring() {
  return getJson<Monitoring>("/api/monitoring", {});
}

export function getTransfers() {
  return getJson<{ files: Transfer[] }>("/api/transfers", { files: [] });
}

export function uploadTransfer(formData: FormData) {
  return postForm<ApiResult>("/api/transfers", formData);
}

export function getInstaller() {
  return getJson<{ script?: string }>("/api/agents/install-script", {});
}

export function startRecording(agentId: string) {
  return postJson<ApiResult>(`/api/recordings/${encodeURIComponent(agentId)}/start`, {});
}

export function stopRecording(agentId: string) {
  return postJson<ApiResult>(`/api/recordings/${encodeURIComponent(agentId)}/stop`, {});
}

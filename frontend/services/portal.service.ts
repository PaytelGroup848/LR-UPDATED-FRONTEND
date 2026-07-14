import type { ApiResult, Id, PortalApp, PortalServer, PortalSession, PortalUser, SessionStats } from "@/types/admin";
import { apiFetch, getJson, postJson } from "./api";

export function getPortalUser() {
  return apiFetch<PortalUser>("/portal/api/me");
}

export function getPortalServers() {
  return apiFetch<{ success?: boolean; servers?: PortalServer[] } | PortalServer[]>("/portal/api/servers")
    .then((data) => (Array.isArray(data) ? data : data.servers || []))
    .catch(() => []);
}

export function getPortalApps() {
  return apiFetch<{ success?: boolean; apps?: PortalApp[] } | PortalApp[]>("/portal/api/apps")
    .then((data) => (Array.isArray(data) ? data : data.apps || []))
    .catch(() => []);
}

export function launchPortalApp(appId: Id, viewMode?: string) {
  return postJson<ApiResult>(`/portal/api/apps/${appId}/launch`, viewMode ? { view_mode: viewMode } : {});
}

export function launchPortalServer(serverId: Id, viewMode?: string) {
  return postJson<ApiResult>("/portal/api/launch", viewMode ? { server_id: serverId, view_mode: viewMode } : { server_id: serverId });
}

export function reconnectPortalSession(sessionId: Id) {
  return postJson<ApiResult>(`/portal/api/sessions/${sessionId}/reconnect`, {});
}

export function getPortalSessions() {
  return apiFetch<{ success?: boolean; sessions?: PortalSession[] } | PortalSession[]>("/portal/api/my-sessions")
    .then((data) => (Array.isArray(data) ? data : data.sessions || []))
    .catch(() => []);
}

export function getPortalStats() {
  return getJson<SessionStats>("/portal/api/sessions/stats", {});
}

import type { Session, SessionStats } from "@/types/admin";
import { apiFetch, getJson } from "./api";

export function getSessions() {
  return apiFetch<{ sessions?: Session[] } | Session[]>("/api/sessions/?status=all")
    .then((data) => (Array.isArray(data) ? data : data.sessions || []))
    .catch(() => []);
}

export function getSessionStats() {
  return getJson<SessionStats>("/api/sessions/stats", {});
}

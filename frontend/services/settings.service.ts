import type { ApiResult, ClipboardItem, LoginLink, Ticket } from "@/types/admin";
import { getJson, patchJson, postJson } from "./api";

export function getTickets() {
  return getJson<{ tickets: Ticket[] }>("/api/tickets?status=all", { tickets: [] });
}

export function createTicket(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/api/tickets", payload);
}

export function closeTicket(id: string | number) {
  return patchJson<ApiResult>(`/api/tickets/${id}`, { status: "closed" });
}

export function getClipboard() {
  return getJson<{ items: ClipboardItem[] }>("/api/clipboard", { items: [] });
}

export function createClipboard(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/api/clipboard", payload);
}

export function sendAlert(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/api/alerts/test", payload);
}

export function getLoginLinks() {
  return getJson<{ links: LoginLink[] }>("/api/login-links", { links: [] });
}

export function generateLoginLink(payload: Record<string, unknown>) {
  return postJson<ApiResult<{ url?: string }>>("/api/generate-url", payload);
}

export function revokeLoginLink(id: string | number) {
  return postJson<ApiResult>(`/api/login-links/${id}/revoke`, {});
}

export function setup2fa() {
  return postJson<{ otpauth_url?: string; qr_code?: string }>("/api/2fa/setup", {});
}

export function enable2fa(payload: Record<string, unknown>) {
  return postJson<ApiResult>("/api/2fa/enable", payload);
}

export function disable2fa() {
  return postJson<ApiResult>("/api/2fa/disable", {});
}

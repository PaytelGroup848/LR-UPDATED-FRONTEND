import type { AuditLog, ErrorLog } from "@/types/admin";
import { getJson } from "./api";

export function getAuditLogs() {
  return getJson<AuditLog[]>("/logs", []);
}

export function getErrorLogs() {
  return getJson<{ errors: ErrorLog[] }>("/api/error-logs", { errors: [] });
}

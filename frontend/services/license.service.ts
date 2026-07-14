import type { ApiResult, LicenseInfo, UserLicenseStatus } from "@/types/admin";
import { apiFetch, getJson, postJson } from "./api";

export function getLicense() {
  return getJson<LicenseInfo>("/api/license", {});
}

export function activateLicense(key: string) {
  return postJson<ApiResult>("/api/license/activate", { key });
}

export function getMyLicense() {
  return apiFetch<UserLicenseStatus>("/license/me");
}

export function activateMyLicense(key: string) {
  return postJson<ApiResult<{ license?: UserLicenseStatus; activation?: unknown }>>("/license/me/activate", { key });
}

export function holdMyLicense(context?: unknown) {
  return postJson<ApiResult<{ license?: UserLicenseStatus }>>("/license/me/hold", { context });
}

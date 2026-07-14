import { browserAwareBaseUrl } from "./url";

const CONFIGURED_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export function apiBaseUrl() {
  return browserAwareBaseUrl(CONFIGURED_API_BASE_URL);
}

export function buildApiUrl(path: string) {
  return `${apiBaseUrl()}${path}`;
}

type RequestOptions = RequestInit & {
  formData?: FormData;
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { formData, headers, ...requestOptions } = options;
  const response = await fetch(buildApiUrl(path), {
    credentials: "include",
    ...requestOptions,
    headers: formData ? headers : { "Content-Type": "application/json", ...headers },
    body: formData || requestOptions.body
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof data === "string" ? data : data?.error || data?.message || data?.detail || "Request failed";
    throw new Error(message);
  }

  return data as T;
}

export function getJson<T>(path: string, fallback: T): Promise<T> {
  return apiFetch<T>(path).catch(() => fallback);
}

export function postJson<T>(path: string, payload: Record<string, unknown>): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function patchJson<T>(path: string, payload: Record<string, unknown>): Promise<T> {
  return apiFetch<T>(path, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function deleteJson<T>(path: string): Promise<T> {
  return apiFetch<T>(path, { method: "DELETE" });
}

export function postForm<T>(path: string, formData: FormData): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    formData
  });
}

import { postJson } from "./api";

export type ConnectionType = "web" | "remoteapp" | "desktop";

export function login(payload: { username: string; password: string; connection_type: ConnectionType }) {
  return postJson<{ success?: boolean; message?: string; redirect?: string; connection_type?: ConnectionType }>("/login", payload);
}

export function register(payload: { username: string; password: string }) {
  return postJson<{ success?: boolean; message?: string }>("/register", payload);
}

export function logout() {
  return postJson<{ success?: boolean }>("/logout", {});
}

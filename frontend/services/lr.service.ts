import type { ApiResult, Id } from "@/types/admin";
import { apiFetch, postJson } from "./api";

export type LrResourceType = "application" | "folder";

export type LrResource = {
  id: Id;
  name: string;
  icon?: string;
  type: LrResourceType;
};

export type LrResourcesResponse = {
  success?: boolean;
  logo?: string;
  applications?: LrResource[];
  folders?: LrResource[];
};

export type LrLaunchResponse = ApiResult<{
  launch_url?: string | null;
  rdp_file_url?: string | null;
  session_id?: string;
  warning?: string;
}>;

export function getMyLrResources() {
  return apiFetch<LrResourcesResponse>("/api/lr/my-resources");
}

export function launchLrResource(resourceId: Id, type: LrResourceType) {
  return postJson<LrLaunchResponse>("/api/lr/launch", {
    resource_id: resourceId,
    type,
    connection_type: "remoteapp"
  });
}

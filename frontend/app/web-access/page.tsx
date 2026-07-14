"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LrFloatingLauncher } from "@/components/remote/LrFloatingLauncher";
import { logout } from "@/services/auth.service";
import {
  getMyLrResources,
  launchLrResource,
  type LrResource
} from "@/services/lr.service";

function WebAccessView() {
  const router = useRouter();
  const [logo, setLogo] = useState("/lr-remote-logo.png");
  const [applications, setApplications] = useState<LrResource[]>([]);
  const [folders, setFolders] = useState<LrResource[]>([]);
  const [launchUrl, setLaunchUrl] = useState<string | null>(null);
  const [launchingId, setLaunchingId] = useState<string | number | null>(null);
  const [message, setMessage] = useState("Select an assigned resource from the launcher.");
  const [error, setError] = useState("");

  async function loadResources() {
    const data = await getMyLrResources();
    setLogo(data.logo || "/lr-remote-logo.png");
    setApplications(data.applications || []);
    setFolders(data.folders || []);
    return [...(data.folders || []), ...(data.applications || [])];
  }

  async function launchResource(resource: LrResource) {
    setError("");
    setMessage(`Opening ${resource.name}...`);
    setLaunchingId(resource.id);
    try {
      const result = await launchLrResource(resource.id, resource.type);
      if (result.success === false || result.error) throw new Error(result.error || "Launch failed.");
      if (!result.launch_url) {
        throw new Error(result.warning || "HTML5 gateway is not configured for this resource.");
      }
      setLaunchUrl(result.launch_url);
      setMessage(result.warning || `${resource.name} is ready.`);
    } catch (launchError) {
      setError(launchError instanceof Error ? launchError.message : "Launch failed.");
      setMessage("Unable to open the selected resource.");
    } finally {
      setLaunchingId(null);
    }
  }

  async function handleLogout() {
    await logout().catch(() => undefined);
    router.replace("/login");
  }

  useEffect(() => {
    let active = true;
    loadResources()
      .then(() => {
        if (!active) return;
        setMessage("Select an assigned resource from the launcher.");
      })
      .catch(() => {
        if (active) router.replace("/login");
      });

    return () => {
      active = false;
    };
  }, [router]);

  return (
    <main className="lr-web-access">
      <div className="lr-guac-stage">
        {launchUrl ? (
          <iframe
            allow="clipboard-read; clipboard-write; fullscreen"
            className="lr-guac-frame"
            src={launchUrl}
            title="LR Remote Session"
          />
        ) : (
          <div className="lr-guac-placeholder">
            <div>{message}</div>
          </div>
        )}
      </div>

      <LrFloatingLauncher
        applications={applications}
        error={error}
        folders={folders}
        launchingId={launchingId}
        logo={logo}
        onLaunch={launchResource}
        onLogout={handleLogout}
      />

      <div className="lr-web-status">{error || message}</div>
    </main>
  );
}

export default function WebAccessPage() {
  return (
    <Suspense fallback={<main className="lr-web-access"><div className="lr-guac-placeholder">Loading...</div></main>}>
      <WebAccessView />
    </Suspense>
  );
}

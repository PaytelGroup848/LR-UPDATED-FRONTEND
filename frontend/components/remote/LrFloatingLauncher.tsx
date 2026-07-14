"use client";

import { useState } from "react";
import type { LrResource } from "@/services/lr.service";

type Props = {
  logo?: string;
  applications: LrResource[];
  folders: LrResource[];
  launchingId?: string | number | null;
  error?: string;
  onLaunch: (resource: LrResource) => void;
  onLogout: () => void;
};

function fallbackIcon(resource: LrResource) {
  return resource.type === "folder" ? "DIR" : "APP";
}

export function LrFloatingLauncher({
  logo,
  applications,
  folders,
  launchingId,
  error,
  onLaunch,
  onLogout
}: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const resources = [...folders, ...applications];

  if (collapsed) {
    return (
      <button className="lr-launcher-tab" onClick={() => setCollapsed(false)} title="Open launcher">
        <span>LR</span>
      </button>
    );
  }

  return (
    <aside className="lr-launcher-panel" aria-label="LR Remote App Launcher">
      <div className="lr-launcher-title">LR Remote App</div>
      <button className="lr-launcher-collapse" onClick={() => setCollapsed(true)} title="Collapse launcher">
        &lt;
      </button>
      <div className="lr-launcher-logo">
        <img alt="LR Remote Access" src={logo || "/lr-remote-logo.png"} />
      </div>

      <div className="lr-launcher-list">
        {resources.length ? (
          resources.map((resource) => {
            const launching = String(launchingId || "") === String(resource.id);
            return (
              <button
                className="lr-launcher-item"
                disabled={launching}
                key={`${resource.type}-${resource.id}`}
                onClick={() => onLaunch(resource)}
                title={resource.name}
              >
                <span className={`lr-launcher-icon ${resource.type}`}>
                  {resource.icon ? <img alt="" src={resource.icon} onError={(event) => { event.currentTarget.style.display = "none"; }} /> : null}
                  <span>{fallbackIcon(resource)}</span>
                </span>
                <span className="lr-launcher-name">{launching ? "Opening..." : resource.name}</span>
              </button>
            );
          })
        ) : (
          <div className="lr-launcher-empty">No assigned resources</div>
        )}
      </div>

      {error ? <div className="lr-launcher-error">{error}</div> : null}

      <button className="lr-launcher-item lr-launcher-logout" onClick={onLogout}>
        <span className="lr-launcher-icon logout">OUT</span>
        <span className="lr-launcher-name">Logoff</span>
      </button>
    </aside>
  );
}

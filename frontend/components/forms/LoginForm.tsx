"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { login, register, type ConnectionType } from "@/services/auth.service";
import { buildApiUrl } from "@/services/api";
import { getPortalApps, getPortalServers, launchPortalApp, launchPortalServer } from "@/services/portal.service";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { formPayload } from "@/utils/form";

type LaunchResult = {
  success?: boolean;
  error?: string;
  message?: string;
  warning?: string;
  launch_url?: string | null;
  rdp_file_url?: string | null;
};

function reserveLaunchWindow() {
  const launchWindow = window.open("about:blank", "_blank");
  if (!launchWindow) return null;

  launchWindow.opener = null;
  launchWindow.document.title = "Connecting";
  launchWindow.document.body.style.margin = "0";
  launchWindow.document.body.style.fontFamily = "Arial, sans-serif";
  launchWindow.document.body.style.background = "#0f172a";
  launchWindow.document.body.style.color = "#f8fafc";
  launchWindow.document.body.innerHTML =
    '<div style="min-height:100vh;display:grid;place-items:center;text-align:center"><div><h1 style="font-size:20px;margin:0 0 8px">Connecting...</h1><p style="margin:0;color:#cbd5e1">Preparing your remote session.</p></div></div>';

  return launchWindow;
}

function openLaunchTarget(launchWindow: Window | null, url?: string | null) {
  if (!url) {
    launchWindow?.close();
    return false;
  }

  if (launchWindow && !launchWindow.closed) {
    launchWindow.location.href = url;
    return true;
  }

  window.location.href = url;
  return true;
}

export function LoginForm() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [connectionType, setConnectionType] = useState<ConnectionType>("remoteapp");
  const [message, setMessage] = useState<FormMessageValue>();
  const [submitting, setSubmitting] = useState(false);

  async function submitLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    let launchWindow: Window | null = null;
    const data = formPayload<{ username: string; password: string }>(event.currentTarget);

    try {
      if (mode === "register") {
        await register(data);
        setMode("login");
        setMessage({ text: "Account created. Login now.", type: "success" });
      } else {
        window.localStorage.setItem("lr_connection_type", connectionType);
        launchWindow = connectionType === "remoteapp" ? null : reserveLaunchWindow();
        await login({ ...data, connection_type: connectionType });

        if (connectionType === "remoteapp") {
          router.push("/web-access");
          return;
        }

        // Web and desktop retain their existing launch behavior. RemoteApp exits
        // above and can never fall through to the server/desktop launcher.
        const viewMode = connectionType === "web" ? "html5" : "full_desktop";
        const apps = await getPortalApps();
        const app = apps[0];
        let launchResult: LaunchResult;
        if (app) {
          launchResult = (await launchPortalApp(app.id, viewMode)) as LaunchResult;
        } else {
          const servers = await getPortalServers();
          const server = servers.find((item) => item.is_active !== false) || servers[0];
          if (!server) {
            launchWindow?.close();
            throw new Error("No active server available. Contact admin.");
          }
          launchResult = (await launchPortalServer(server.id, viewMode)) as LaunchResult;
        }
        if (launchResult.success === false || launchResult.error) {
          throw new Error(launchResult.error || "Remote session launch failed.");
        }
        if (!openLaunchTarget(launchWindow, launchResult.launch_url || launchResult.rdp_file_url)) {
          throw new Error(launchResult.warning || launchResult.message || "Remote session URL not available.");
        }
      }
    } catch (error) {
      launchWindow?.close();
      setMessage({ text: error instanceof Error ? error.message : "Request failed.", type: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-brand">
        <div>
          <img alt="LR Remote Access" className="auth-logo" src="/lr-remote-logo.png" />
          <p>Secure portal for launching remote sessions, tracking active connections, and monitoring connected agents.</p>
        </div>
        <div className="auth-footer">
          <a className="auth-download-btn" href={buildApiUrl("/portal/api/download-client")}>
            Download Desktop App
          </a>
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-tabs">
          <button className={`auth-tab ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")} type="button">
            Login
          </button>
          <button className={`auth-tab ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")} type="button">
            Register
          </button>
        </div>
        <div className="auth-title">{mode === "login" ? "Welcome back" : "Create account"}</div>
        <div className="auth-sub">{mode === "login" ? "Sign in to open your portal." : "Create a panel user, then sign in."}</div>
        <form onSubmit={submitLogin}>
          <div className="field">
            <label>Username</label>
            <input autoComplete="username" name="username" required />
          </div>
          <div className="field">
            <label>Password</label>
            <input autoComplete={mode === "login" ? "current-password" : "new-password"} name="password" required type="password" />
          </div>
          {mode === "login" ? (
            <div className="field">
              <label>View mode</label>
              <div className="auth-view-options">
                <label className={connectionType === "remoteapp" ? "active" : ""}>
                  <input
                    checked={connectionType === "remoteapp"}
                    name="connection_type"
                    onChange={() => setConnectionType("remoteapp")}
                    type="radio"
                    value="remoteapp"
                  />
                  <span>Remote App View</span>
                </label>
                <label className={connectionType === "desktop" ? "active" : ""}>
                  <input
                    checked={connectionType === "desktop"}
                    name="connection_type"
                    onChange={() => setConnectionType("desktop")}
                    type="radio"
                    value="desktop"
                  />
                  <span>Desktop View</span>
                </label>
                <label className={connectionType === "web" ? "active" : ""}>
                  <input
                    checked={connectionType === "web"}
                    name="connection_type"
                    onChange={() => setConnectionType("web")}
                    type="radio"
                    value="web"
                  />
                  <span>Web View</span>
                </label>
              </div>
            </div>
          ) : null}
          <Button disabled={submitting} type="submit" variant="green">
            {submitting ? "Please wait..." : mode === "login" ? "Login" : "Register"}
          </Button>
          <FormMessage message={message} />
        </form>
      </section>
    </main>
  );
}

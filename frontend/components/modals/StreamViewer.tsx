"use client";

import { useEffect, useRef, useState } from "react";
import { io, type Socket } from "socket.io-client";
import type { Agent } from "@/types/admin";
import { Button } from "@/components/ui/Button";
import { browserAwareBaseUrl } from "@/services/url";

const CONFIGURED_SOCKET_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

type StreamViewerProps = {
  agent?: Agent | null;
  sessionId?: string | null;
  onClose: () => void;
};

function socketBaseUrl() {
  return browserAwareBaseUrl(CONFIGURED_SOCKET_URL) || undefined;
}

function normalizeFrame(frameValue?: string) {
  if (!frameValue) return "";
  if (frameValue.startsWith("data:")) return frameValue;
  return `data:image/jpeg;base64,${frameValue}`;
}

function frameBlobUrl(frameValue: Blob | ArrayBuffer | Uint8Array | number[]) {
  if (frameValue instanceof Blob) return URL.createObjectURL(frameValue);
  const bytes = frameValue instanceof Uint8Array ? frameValue : new Uint8Array(frameValue as ArrayBuffer | number[]);
  return URL.createObjectURL(new Blob([bytes], { type: "image/jpeg" }));
}

function normalizeKey(key: string) {
  const map: Record<string, string> = {
    Enter: "enter",
    Escape: "esc",
    Backspace: "backspace",
    Tab: "tab",
    Delete: "delete",
    ArrowUp: "up",
    ArrowDown: "down",
    ArrowLeft: "left",
    ArrowRight: "right",
    " ": "space",
    Control: "control",
    Alt: "alt",
    Meta: "meta"
  };

  return map[key] || key.toLowerCase();
}

export function StreamViewer({ agent, sessionId, onClose }: StreamViewerProps) {
  const socketRef = useRef<Socket | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const frameUrlRef = useRef("");
  const [frame, setFrame] = useState("");
  const [status, setStatus] = useState("Ready.");
  const [quality, setQuality] = useState(55);
  const [fps, setFps] = useState(8);

  useEffect(() => {
    if (!agent) return;

    const socket = io(socketBaseUrl(), { withCredentials: true });
    socketRef.current = socket;

    socket.on("connect", () => {
      setStatus("Connected.");
      socket.emit("viewer_join_stream", { agent_id: agent.agent_id, session_id: sessionId || undefined });
    });
    socket.on("disconnect", () => setStatus("Disconnected."));
    socket.on("viewer_stream_result", (payload: { success?: boolean; error?: string; action?: string }) => {
      if (!payload.success) setStatus(payload.error || "Stream access denied.");
    });
    socket.on("screen_update", (payload: { agent_id?: string; frame?: string }) => {
      if (payload.agent_id === agent.agent_id && payload.frame) {
        if (frameUrlRef.current) {
          URL.revokeObjectURL(frameUrlRef.current);
          frameUrlRef.current = "";
        }
        setFrame(normalizeFrame(payload.frame));
        setStatus(`Live frame received at ${new Date().toLocaleTimeString()}.`);
      }
    });
    socket.on(
      "screen_update_binary",
      (payload: { agent_id?: string; frame?: Blob | ArrayBuffer | Uint8Array | number[]; sent_at?: number }) => {
        if (payload.agent_id !== agent.agent_id || !payload.frame) return;
        if (frameUrlRef.current) URL.revokeObjectURL(frameUrlRef.current);
        const nextUrl = frameBlobUrl(payload.frame);
        frameUrlRef.current = nextUrl;
        setFrame(nextUrl);
        const latency = payload.sent_at ? Math.max(0, Math.round(Date.now() - payload.sent_at * 1000)) : null;
        setStatus(latency === null ? "Live frame received." : `Live frame received. ${latency} ms`);
      }
    );
    socket.on("stream_control_result", (payload: { success?: boolean; error?: string; action?: string }) => {
      setStatus(payload.success ? `Stream ${payload.action || "control"} sent.` : payload.error || "Stream control failed.");
    });
    socket.on("screen_error", (payload: { agent_id?: string; error?: string }) => {
      if (payload.agent_id === agent.agent_id) setStatus(payload.error || "Screen stream error.");
    });

    return () => {
      socket.emit("admin_stop_agent_stream", { agent_id: agent.agent_id, session_id: sessionId || undefined });
      socket.emit("viewer_leave_stream", { agent_id: agent.agent_id, session_id: sessionId || undefined });
      socket.disconnect();
      socketRef.current = null;
      if (frameUrlRef.current) {
        URL.revokeObjectURL(frameUrlRef.current);
        frameUrlRef.current = "";
      }
    };
  }, [agent, sessionId]);

  if (!agent) return null;

  function emitInput(eventName: string, payload: Record<string, unknown>) {
    socketRef.current?.emit(eventName, { agent_id: agent?.agent_id, session_id: sessionId || undefined, ...payload });
  }

  function startStream() {
    emitInput("admin_start_agent_stream", { settings: { quality, fps, transport: "binary", adaptive: true } });
    setStatus("Stream requested.");
  }

  function stopStream() {
    emitInput("admin_stop_agent_stream", {});
    setStatus("Stream stopped.");
  }

  function remoteCoordinates(event: React.MouseEvent) {
    const image = imageRef.current;
    if (!image) return null;

    const rect = image.getBoundingClientRect();
    const width = image.naturalWidth || 1280;
    const height = image.naturalHeight || 720;

    return {
      x: Math.round((event.clientX - rect.left) * (width / rect.width)),
      y: Math.round((event.clientY - rect.top) * (height / rect.height))
    };
  }

  function sendMouse(event: React.MouseEvent, action: string, extra: Record<string, unknown> = {}) {
    const coords = remoteCoordinates(event);
    if (!coords) return;
    emitInput("viewer_mouse_event", { action, ...coords, ...extra });
  }

  function sendKey(event: React.KeyboardEvent) {
    event.preventDefault();
    emitInput("viewer_keyboard_event", {
      action: "press",
      key: normalizeKey(event.key),
      ctrl: event.ctrlKey,
      alt: event.altKey,
      shift: event.shiftKey,
      meta: event.metaKey
    });
  }

  return (
    <div className="stream-modal">
      <div className="stream-shell">
        <div className="stream-top">
          <div className="stream-title">{agent.hostname || agent.agent_id}</div>
          <div className="stream-controls">
            <input
              aria-label="Stream quality"
              max="95"
              min="20"
              onChange={(event) => setQuality(Number(event.target.value))}
              type="number"
              value={quality}
            />
            <input
              aria-label="Stream FPS"
              max="30"
              min="1"
              onChange={(event) => setFps(Number(event.target.value))}
              type="number"
              value={fps}
            />
            <Button type="button" variant="green" onClick={startStream}>
              Start
            </Button>
            <Button type="button" onClick={stopStream}>
              Stop
            </Button>
            <Button type="button" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
        <div
          className="stream-stage"
          onClick={(event) => sendMouse(event, "click")}
          onKeyDown={sendKey}
          onMouseMove={(event) => sendMouse(event, "move")}
          tabIndex={0}
        >
          {frame ? (
            <img alt="Remote stream" ref={imageRef} src={frame} />
          ) : (
            <div className="stream-placeholder">Waiting for stream frame...</div>
          )}
        </div>
        <div className="stream-status">{status}</div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import type { Server } from "@/types/admin";
import { createApplication, uploadApplication } from "@/services/application.service";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";
import { formPayload } from "@/utils/form";

export function ApplicationForm({ servers, onSaved }: { servers: Server[]; onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitApp(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = formPayload<Record<string, unknown>>(event.currentTarget);
    const itemType = String(data.item_type || "remote_app");
    const displayMode = String(data.display_mode || "remote_app");
    const target = String(data.target || "");
    const payload = {
      name: data.name,
      server_id: data.server_id,
      icon: itemType === "folder" ? "folder" : data.name,
      item_type: itemType,
      display_mode: displayMode,
      description: data.description,
      working_directory: data.working_directory,
      arguments: itemType === "folder" ? target : data.arguments,
      initial_program: itemType === "folder" ? "explorer.exe" : undefined,
      launch_mode:
        displayMode === "full_desktop" || itemType === "desktop"
          ? "desktop"
          : itemType === "folder"
            ? "initial_program"
            : "remote_app",
      remote_app_program: itemType === "remote_app" || displayMode === "seamless" ? target : "",
      folder_path: itemType === "folder" ? target : "",
      target
    };

    try {
      await createApplication(payload);
      event.currentTarget.reset();
      setMessage({ text: "Item published successfully.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to publish item.", type: "error" });
    }
  }

  return (
    <Panel
      title="Publish access item"
      hint="Choose the TSplus-style view mode users should get when they launch this item."
    >
      <form onSubmit={submitApp}>
        <div className="field">
          <label>Name shown to user</label>
          <input name="name" placeholder="Tally Prime" required />
        </div>
        <div className="field">
          <label>Windows VPS</label>
          <select name="server_id" required>
            <option value="">Select VPS</option>
            {servers.map((server) => (
              <option key={server.id} value={server.id}>
                {server.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Display mode</label>
          <select name="display_mode">
            <option value="remote_app">RemoteApp View</option>
            <option value="full_desktop">Remote Desktop</option>
            <option value="seamless">Seamless View</option>
            <option value="html5">HTML5 Web Access</option>
          </select>
        </div>
        <div className="field">
          <label>Published item type</label>
          <select name="item_type">
            <option value="remote_app">Remote app</option>
            <option value="folder">Folder</option>
            <option value="desktop">Full desktop</option>
          </select>
        </div>
        <div className="field">
          <label>RemoteApp program / folder path</label>
          <input name="target" placeholder="||AppName or C:\\Program Files\\App\\app.exe" />
        </div>
        <div className="field">
          <label>Description</label>
          <textarea name="description" />
        </div>
        <div className="row">
          <div className="field">
            <label>Working directory</label>
            <input name="working_directory" />
          </div>
          <div className="field">
            <label>Arguments</label>
            <input name="arguments" />
          </div>
        </div>
        <Button type="submit" variant="green">
          Publish Item
        </Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

export function SoftwareUploadForm({ onSaved }: { onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await uploadApplication(new FormData(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "Software uploaded successfully.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to upload software.", type: "error" });
    }
  }

  return (
    <Panel title="Upload software">
      <form onSubmit={submitUpload}>
        <div className="field">
          <label>Installer file</label>
          <input name="file" required type="file" />
        </div>
        <Button type="submit">Upload</Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

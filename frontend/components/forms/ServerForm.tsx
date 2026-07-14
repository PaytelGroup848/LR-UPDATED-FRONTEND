"use client";

import { useState } from "react";
import { createServer } from "@/services/application.service";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";
import { formPayload } from "@/utils/form";

export function ServerForm({ onSaved }: { onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitServer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await createServer(formPayload(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "VPS added successfully.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to add VPS.", type: "error" });
    }
  }

  return (
    <Panel
      title="Add Windows VPS"
      hint="Add the VPS where Tally or other applications are installed. Use the Windows RDP port, normally 3389."
    >
      <form onSubmit={submitServer}>
        <div className="field">
          <label>Display name</label>
          <input name="name" placeholder="Tally VPS" required />
        </div>
        <div className="field">
          <label>Host / IP</label>
          <input name="host" placeholder="203.0.113.10" required />
        </div>
        <div className="row">
          <div className="field">
            <label>RDP username</label>
            <input name="username" required />
          </div>
          <div className="field">
            <label>RDP port</label>
            <input name="port" required type="number" defaultValue="3389" />
          </div>
        </div>
        <div className="field">
          <label>RDP password</label>
          <input name="password" required type="password" />
        </div>
        <Button type="submit" variant="green">
          Add VPS
        </Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

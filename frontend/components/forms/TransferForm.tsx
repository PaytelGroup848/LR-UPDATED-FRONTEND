"use client";

import { useState } from "react";
import { uploadTransfer } from "@/services/monitoring.service";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";

export function TransferForm({ onSaved }: { onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitTransfer(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await uploadTransfer(new FormData(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "File uploaded.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to upload file.", type: "error" });
    }
  }

  return (
    <Panel title="Upload file">
      <form onSubmit={submitTransfer}>
        <div className="field">
          <label>User</label>
          <input name="username" />
        </div>
        <div className="field">
          <label>File</label>
          <input name="file" required type="file" />
        </div>
        <Button type="submit">Upload File</Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

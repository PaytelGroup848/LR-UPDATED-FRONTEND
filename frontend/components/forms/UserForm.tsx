"use client";

import { useState } from "react";
import { createUser, importUsersCsv } from "@/services/user.service";
import { formPayload } from "@/utils/form";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";

export function UserForm({ onSaved }: { onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitUser(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await createUser(formPayload(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "User created successfully.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to create user.", type: "error" });
    }
  }

  return (
    <Panel
      title="Create Windows User Account"
      hint="This creates the Windows account used for published apps and stores it for isolated RDP sessions."
    >
      <form onSubmit={submitUser}>
        <div className="field">
          <label>Windows username</label>
          <input name="username" required />
        </div>
        <div className="field">
          <label>Windows password</label>
          <input name="password" required type="password" />
        </div>
        <div className="field">
          <label>Role</label>
          <select name="role">
            <option>User</option>
            <option>Viewer</option>
            <option>Manager</option>
            <option>Admin</option>
            <option>Super Admin</option>
          </select>
        </div>
        <div className="field">
          <label>Alternate RDP username</label>
          <input name="windows_username" placeholder="Optional, defaults to username" />
        </div>
        <div className="field">
          <label>Alternate RDP password</label>
          <input name="windows_password" type="password" />
        </div>
        <div className="field">
          <label>Windows domain</label>
          <input name="windows_domain" placeholder="Optional" />
        </div>
        <label className="checkbox-row">
          <input defaultChecked name="windows_account_enabled" type="checkbox" value="true" />
          Create and use this Windows account for isolated sessions
        </label>
        <Button type="submit" variant="green">
          Create Windows User Account
        </Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

export function UserImportForm({ onSaved }: { onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await importUsersCsv(new FormData(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "CSV imported successfully.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to import CSV.", type: "error" });
    }
  }

  return (
    <form className="toolbar" onSubmit={submitImport}>
      <input accept=".csv" name="file" required type="file" />
      <Button type="submit">Import CSV</Button>
      <FormMessage message={message} />
    </form>
  );
}

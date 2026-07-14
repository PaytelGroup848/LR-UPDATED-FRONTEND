"use client";

import { useState } from "react";
import type { Application, User } from "@/types/admin";
import { assignApplication } from "@/services/assignment.service";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";
import { formPayload } from "@/utils/form";

export function AssignmentForm({
  applications,
  users,
  onSaved
}: {
  applications: Application[];
  users: User[];
  onSaved: () => void;
}) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitAssign(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = formPayload<{ app_id: string; user_id: string }>(event.currentTarget);

    try {
      await assignApplication(data.app_id, data.user_id);
      setMessage({ text: "Assignment saved.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to assign item.", type: "error" });
    }
  }

  return (
    <Panel title="Assign app or folder" hint="Choose the published item and the user who should see it.">
      <form onSubmit={submitAssign}>
        <div className="field">
          <label>Published item</label>
          <select name="app_id" required>
            <option value="">Select item</option>
            {applications.map((app) => (
              <option key={app.id} value={app.id}>
                {app.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>User</label>
          <select name="user_id" required>
            <option value="">Select user</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.username}
              </option>
            ))}
          </select>
        </div>
        <Button type="submit" variant="green">
          Assign
        </Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

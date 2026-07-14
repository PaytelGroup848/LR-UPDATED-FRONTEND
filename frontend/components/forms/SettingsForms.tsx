"use client";

import { useState } from "react";
import {
  createClipboard,
  createTicket,
  disable2fa,
  enable2fa,
  generateLoginLink,
  sendAlert,
  setup2fa
} from "@/services/settings.service";
import type { User } from "@/types/admin";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";
import { formPayload } from "@/utils/form";

type FormProps = {
  onSaved: () => void;
};

export function TicketForm({ onSaved }: FormProps) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitTicket(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await createTicket(formPayload(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "Ticket created.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to create ticket.", type: "error" });
    }
  }

  return (
    <Panel title="Create ticket">
      <form onSubmit={submitTicket}>
        <div className="field">
          <label>Username</label>
          <input name="username" />
        </div>
        <div className="field">
          <label>Title</label>
          <input name="title" required />
        </div>
        <div className="field">
          <label>Priority</label>
          <select name="priority">
            <option>normal</option>
            <option>critical</option>
            <option>low</option>
          </select>
        </div>
        <div className="field">
          <label>Description</label>
          <textarea name="description" />
        </div>
        <Button type="submit">Create Ticket</Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

export function ClipboardForm({ onSaved }: FormProps) {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitClipboard(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await createClipboard(formPayload(event.currentTarget));
      event.currentTarget.reset();
      setMessage({ text: "Clipboard item saved.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to save clipboard.", type: "error" });
    }
  }

  return (
    <Panel title="Clipboard push">
      <form onSubmit={submitClipboard}>
        <div className="field">
          <label>Username</label>
          <input name="username" />
        </div>
        <div className="field">
          <label>Content</label>
          <textarea name="content" required />
        </div>
        <Button type="submit">Send Clipboard</Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

export function AlertForm() {
  const [message, setMessage] = useState<FormMessageValue>();

  async function submitAlert(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await sendAlert(formPayload(event.currentTarget));
      setMessage({ text: "Alert sent.", type: "success" });
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to send alert.", type: "error" });
    }
  }

  return (
    <Panel title="Test alert">
      <form onSubmit={submitAlert}>
        <div className="field">
          <label>Subject</label>
          <input name="subject" defaultValue="LR Remote Access test alert" />
        </div>
        <div className="field">
          <label>Severity</label>
          <select name="severity">
            <option>info</option>
            <option>normal</option>
            <option>critical</option>
          </select>
        </div>
        <div className="field">
          <label>Message</label>
          <textarea name="message" defaultValue="Alerting is configured." />
        </div>
        <Button type="submit">Send Alert</Button>
        <FormMessage message={message} />
      </form>
    </Panel>
  );
}

export function LoginLinkForm({ users, onSaved }: { users: User[]; onSaved: () => void }) {
  const [message, setMessage] = useState<FormMessageValue>();
  const [url, setUrl] = useState("");

  async function submitLoginLink(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      const data = await generateLoginLink(formPayload(event.currentTarget));
      setUrl(data.url || "");
      setMessage({ text: "Login URL generated.", type: "success" });
      onSaved();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to generate login URL.", type: "error" });
    }
  }

  return (
    <Panel title="Generate login URL">
      <form onSubmit={submitLoginLink}>
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
        <div className="field">
          <label>Expires in minutes</label>
          <input name="expires_minutes" type="number" defaultValue="60" />
        </div>
        <Button type="submit">Generate URL</Button>
        <FormMessage message={message} />
        {url ? <div className="code">{url}</div> : null}
      </form>
    </Panel>
  );
}

export function TwoFactorForm() {
  const [message, setMessage] = useState<FormMessageValue>();
  const [setupText, setSetupText] = useState("");

  async function requestSetup() {
    try {
      const data = await setup2fa();
      setSetupText(data.otpauth_url || data.qr_code || "Setup generated.");
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to setup 2FA.", type: "error" });
    }
  }

  async function submitEnable(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      await enable2fa(formPayload(event.currentTarget));
      setMessage({ text: "2FA enabled.", type: "success" });
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to enable 2FA.", type: "error" });
    }
  }

  async function requestDisable() {
    try {
      await disable2fa();
      setMessage({ text: "2FA disabled.", type: "success" });
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to disable 2FA.", type: "error" });
    }
  }

  return (
    <Panel title="Two-factor authentication">
      <div className="actions">
        <Button type="button" onClick={requestSetup}>
          Setup 2FA
        </Button>
        <Button type="button" onClick={requestDisable}>
          Disable 2FA
        </Button>
      </div>
      <form onSubmit={submitEnable}>
        <div className="field">
          <label>Code</label>
          <input name="code" />
        </div>
        <Button type="submit" variant="green">
          Enable 2FA
        </Button>
      </form>
      <FormMessage message={message} />
      {setupText ? <div className="code">{setupText}</div> : null}
    </Panel>
  );
}

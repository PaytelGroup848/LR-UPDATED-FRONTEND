"use client";

import { useEffect, useState } from "react";
import type { ClipboardItem, LoginLink, Ticket } from "@/types/admin";
import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/tables/DataTable";
import { Panel } from "@/components/ui/Panel";
import { AlertForm, ClipboardForm, LoginLinkForm, TicketForm, TwoFactorForm } from "@/components/forms/SettingsForms";
import { closeTicket, getClipboard, getLoginLinks, getTickets, revokeLoginLink } from "@/services/settings.service";
import { useAdminData } from "@/hooks/useAdminData";
import { formatDate } from "@/utils/format";

export default function SettingsPage() {
  const { users } = useAdminData();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [clipboard, setClipboard] = useState<ClipboardItem[]>([]);
  const [links, setLinks] = useState<LoginLink[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    const [ticketData, clipboardData, linkData] = await Promise.all([getTickets(), getClipboard(), getLoginLinks()]);
    setTickets(ticketData.tickets || []);
    setClipboard(clipboardData.items || []);
    setLinks(linkData.links || []);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function requestCloseTicket(id: string | number) {
    await closeTicket(id);
    refresh();
  }

  async function requestRevokeLink(id: string | number) {
    await revokeLoginLink(id);
    refresh();
  }

  return (
    <AdminShell>
      <PageHeader title="Settings" description="Security, login URLs, tickets, clipboard, and alert tools." action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <div className="layout">
        <div className="stack">
          <TwoFactorForm />
          <LoginLinkForm users={users} onSaved={refresh} />
          <TicketForm onSaved={refresh} />
          <ClipboardForm onSaved={refresh} />
          <AlertForm />
        </div>
        <div className="stack">
          <Panel title="Tickets">
            <DataTable
              rows={tickets}
              emptyMessage="No tickets found."
              getKey={(row) => row.id}
              columns={[
                { header: "User", cell: (row) => row.username || "-" },
                { header: "Subject", cell: (row) => row.title || row.subject || row.description || row.message || "-" },
                { header: "Status", cell: (row) => <Badge value={row.status || "open"} /> },
                { header: "Created", cell: (row) => formatDate(row.created_at) },
                { header: "Action", cell: (row) => <Button onClick={() => requestCloseTicket(row.id)}>Close</Button> }
              ]}
            />
          </Panel>
          <Panel title="Login URLs">
            <DataTable
              rows={links}
              emptyMessage="No login URLs generated."
              getKey={(row) => row.id}
              columns={[
                { header: "User", cell: (row) => row.username || "-" },
                { header: "URL", cell: (row) => row.url || "-" },
                { header: "Expires", cell: (row) => formatDate(row.expires_at) },
                { header: "Status", cell: (row) => <Badge value={row.revoked ? "closed" : "active"} /> },
                { header: "Action", cell: (row) => <Button onClick={() => requestRevokeLink(row.id)}>Revoke</Button> }
              ]}
            />
          </Panel>
          <Panel title="Clipboard history">
            <DataTable
              rows={clipboard}
              emptyMessage="No clipboard items found."
              getKey={(row, index) => row.id || index}
              columns={[
                { header: "User", cell: (row) => row.username || "-" },
                { header: "Content", cell: (row) => row.content || "-" },
                { header: "Created", cell: (row) => formatDate(row.created_at) }
              ]}
            />
          </Panel>
        </div>
      </div>
    </AdminShell>
  );
}

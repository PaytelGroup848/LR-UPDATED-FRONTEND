"use client";

import { useEffect, useState } from "react";
import type { AuditLog, ErrorLog } from "@/types/admin";
import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/tables/DataTable";
import { Panel } from "@/components/ui/Panel";
import { getAuditLogs, getErrorLogs } from "@/services/log.service";
import { formatDate } from "@/utils/format";

export default function LogsPage() {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    const [audit, errors] = await Promise.all([getAuditLogs(), getErrorLogs()]);
    setAuditLogs(audit);
    setErrorLogs(errors.errors || []);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <AdminShell>
      <PageHeader title="Logs" description="Audit activity and backend error logs." action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <div className="stack">
        <Panel title="Audit logs">
          <DataTable
            rows={auditLogs}
            emptyMessage="No audit logs found."
            getKey={(row, index) => row.id || index}
            columns={[
              { header: "User", cell: (row) => row.username || "-" },
              { header: "Action", cell: (row) => row.action || "-" },
              { header: "IP", cell: (row) => row.ip_address || "-" },
              { header: "Date", cell: (row) => formatDate(row.created_at) }
            ]}
          />
        </Panel>
        <Panel title="Error logs">
          <DataTable
            rows={errorLogs}
            emptyMessage="No error logs found."
            getKey={(row, index) => row.id || index}
            columns={[
              { header: "Level", cell: (row) => <Badge value={row.level || "normal"} /> },
              { header: "Message", cell: (row) => row.message || "-" },
              { header: "Date", cell: (row) => formatDate(row.created_at) }
            ]}
          />
        </Panel>
      </div>
    </AdminShell>
  );
}

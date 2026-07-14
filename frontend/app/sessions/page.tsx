"use client";

import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/tables/DataTable";
import { useAdminData } from "@/hooks/useAdminData";
import { formatDate } from "@/utils/format";

export default function SessionsPage() {
  const { sessions, stats, loading, refresh } = useAdminData();

  return (
    <AdminShell>
      <PageHeader title="Sessions" description={`Active sessions: ${stats.active || 0}`} action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <DataTable
        rows={sessions}
        emptyMessage="No sessions found."
        getKey={(row) => row.id}
        columns={[
          { header: "User", cell: (row) => row.username || row.user_id || "-" },
          { header: "Application", cell: (row) => row.app_name || row.application_name || "-" },
          { header: "Server", cell: (row) => row.server_name || "-" },
          { header: "Status", cell: (row) => <Badge value={row.status} /> },
          { header: "Started", cell: (row) => formatDate(row.started_at) },
          { header: "Ended", cell: (row) => formatDate(row.ended_at) }
        ]}
      />
    </AdminShell>
  );
}

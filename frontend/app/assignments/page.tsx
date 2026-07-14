"use client";

import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/tables/DataTable";
import { AssignmentForm } from "@/components/forms/AssignmentForm";
import { useAdminData } from "@/hooks/useAdminData";
import { unassignApplication } from "@/services/assignment.service";

export default function AssignmentsPage() {
  const { users, applications, loading, refresh } = useAdminData();
  const rows = applications.flatMap((app) =>
    (app.assigned_users || []).map((user) => ({
      appId: app.id,
      appName: app.name,
      userId: user.id,
      username: user.username,
      role: user.role
    }))
  );

  async function removeAssignment(appId: string | number, userId: string | number) {
    await unassignApplication(appId, userId);
    refresh();
  }

  return (
    <AdminShell>
      <PageHeader title="Assignments" description="Control which users can see each published app or folder." action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <div className="layout">
        <AssignmentForm applications={applications} users={users} onSaved={refresh} />
        <DataTable
          rows={rows}
          emptyMessage="No assignments found."
          getKey={(row) => `${row.appId}-${row.userId}`}
          columns={[
            { header: "Published item", cell: (row) => row.appName },
            { header: "User", cell: (row) => row.username },
            { header: "Role", cell: (row) => row.role || "-" },
            { header: "Action", cell: (row) => <Button onClick={() => removeAssignment(row.appId, row.userId)}>Unassign</Button> }
          ]}
        />
      </div>
    </AdminShell>
  );
}

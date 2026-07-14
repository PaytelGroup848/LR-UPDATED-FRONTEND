"use client";

import type { Id } from "@/types/admin";
import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/tables/DataTable";
import { ApplicationForm, SoftwareUploadForm } from "@/components/forms/ApplicationForm";
import { ServerForm } from "@/components/forms/ServerForm";
import { useAdminData } from "@/hooks/useAdminData";
import { deleteApplication, testRdp, updateApplication } from "@/services/application.service";

function modeLabel(mode?: string) {
  const labels: Record<string, string> = {
    full_desktop: "Remote Desktop",
    remote_app: "RemoteApp",
    seamless: "Seamless",
    html5: "HTML5"
  };
  return labels[String(mode || "")] || mode || "RemoteApp";
}

export default function ApplicationsPage() {
  const { servers, applications, loading, refresh } = useAdminData();

  async function editApp(id: Id) {
    const app = applications.find((item) => item.id === id);
    if (!app) return;

    const name = window.prompt("Software name", app.name);
    if (!name) return;
    const description = window.prompt("Description", app.description || "") || "";

    await updateApplication(id, { name, description });
    refresh();
  }

  async function removeApp(id: Id) {
    if (!window.confirm("Delete this published item?")) return;
    await deleteApplication(id);
    refresh();
  }

  async function requestRdpTest(id: Id) {
    const result = await testRdp(id);
    window.alert(result.message || "RDP test requested.");
  }

  return (
    <AdminShell>
      <PageHeader title="Applications" description="Register Windows VPS servers and publish RemoteApps, folders, or desktop access." action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <div className="layout">
        <div className="stack">
          <ServerForm onSaved={refresh} />
          <ApplicationForm servers={servers} onSaved={refresh} />
          <SoftwareUploadForm onSaved={refresh} />
        </div>
        <div className="stack">
          <section className="panel">
            <h2>Windows VPS</h2>
            <DataTable
              rows={servers}
              getKey={(row) => row.id}
              emptyMessage="No servers registered."
              columns={[
                { header: "Name", cell: (row) => row.name },
                { header: "Host", cell: (row) => `${row.host || row.ip_address || "-"}${row.port ? `:${row.port}` : ""}` },
                { header: "Status", cell: (row) => <Badge value={row.status || "normal"} /> },
                { header: "Actions", cell: (row) => <Button onClick={() => requestRdpTest(row.id)}>RDP Test</Button> }
              ]}
            />
          </section>
          <section className="panel">
            <h2>Published items</h2>
            <DataTable
              rows={applications}
              getKey={(row) => row.id}
              emptyMessage="No applications published."
              columns={[
                { header: "Name", cell: (row) => row.name },
                { header: "Mode", cell: (row) => modeLabel(row.display_mode) },
                { header: "Type", cell: (row) => row.item_type || "remote_app" },
                { header: "Server", cell: (row) => row.server_name || row.server_id || "-" },
                { header: "Target", cell: (row) => row.target || row.remote_app_program || row.folder_path || "-" },
                {
                  header: "Actions",
                  cell: (row) => (
                    <div className="actions">
                      <Button onClick={() => editApp(row.id)}>Edit</Button>
                      <Button onClick={() => removeApp(row.id)} variant="danger">
                        Delete
                      </Button>
                    </div>
                  )
                }
              ]}
            />
          </section>
        </div>
      </div>
    </AdminShell>
  );
}

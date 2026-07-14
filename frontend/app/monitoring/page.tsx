"use client";

import { useEffect, useState } from "react";
import type { Agent, Transfer } from "@/types/admin";
import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/tables/DataTable";
import { Panel } from "@/components/ui/Panel";
import { StreamViewer } from "@/components/modals/StreamViewer";
import { TransferForm } from "@/components/forms/TransferForm";
import { getInstaller, getTransfers, startRecording, stopRecording } from "@/services/monitoring.service";
import { useAdminData } from "@/hooks/useAdminData";
import { formatBytes, formatDate } from "@/utils/format";

export default function MonitoringPage() {
  const { agents, monitoring, loading, refresh } = useAdminData();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [installer, setInstaller] = useState("");
  const [transfers, setTransfers] = useState<Transfer[]>([]);

  async function refreshExtras() {
    const transferData = await getTransfers();
    setTransfers(transferData.files || []);
  }

  useEffect(() => {
    refreshExtras();
  }, []);

  async function loadInstaller() {
    const data = await getInstaller();
    setInstaller(data.script || "");
  }

  async function requestRecording(agent: Agent, action: "start" | "stop") {
    if (action === "start") await startRecording(agent.agent_id);
    else await stopRecording(agent.agent_id);
    refresh();
  }

  return (
    <AdminShell>
      <PageHeader title="Monitoring" description="Watch agents, health data, recordings, installers, and file transfers." action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <div className="stack">
        <Panel title="Agents">
          <DataTable
            rows={agents}
            getKey={(row) => row.agent_id}
            emptyMessage="No agents connected."
            columns={[
              { header: "Host", cell: (row) => row.hostname || row.agent_id },
              { header: "User", cell: (row) => row.username || "-" },
              { header: "Status", cell: (row) => <Badge value={row.status} /> },
              { header: "Last seen", cell: (row) => formatDate(row.last_seen) },
              {
                header: "Actions",
                cell: (row) => (
                  <div className="actions">
                    <Button onClick={() => setSelectedAgent(row)}>View</Button>
                    <Button onClick={() => requestRecording(row, "start")}>Record</Button>
                    <Button onClick={() => requestRecording(row, "stop")}>Stop</Button>
                  </div>
                )
              }
            ]}
          />
        </Panel>

        <div className="layout">
          <Panel title="System health">
            <div className="code">{JSON.stringify(monitoring.health || {}, null, 2)}</div>
          </Panel>
          <Panel title="Containers and pods">
            <div className="code">{JSON.stringify({ docker: monitoring.docker, kubernetes: monitoring.kubernetes }, null, 2)}</div>
          </Panel>
        </div>

        <div className="layout">
          <TransferForm onSaved={refreshExtras} />
          <Panel title="Files">
            <DataTable
              rows={transfers}
              emptyMessage="No files uploaded."
              getKey={(row, index) => row.id || index}
              columns={[
                { header: "File", cell: (row) => row.original_name || row.filename || "-" },
                { header: "User", cell: (row) => row.username || "-" },
                { header: "Size", cell: (row) => formatBytes(row.size) },
                { header: "Uploaded", cell: (row) => formatDate(row.uploaded_at) }
              ]}
            />
          </Panel>
        </div>

        <Panel title="Agent installer">
          <div className="actions">
            <Button onClick={loadInstaller}>Load Installer Script</Button>
          </div>
          {installer ? <div className="code">{installer}</div> : null}
        </Panel>
      </div>
      <StreamViewer agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
    </AdminShell>
  );
}

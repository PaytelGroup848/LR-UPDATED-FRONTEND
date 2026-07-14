"use client";

import { useEffect, useState } from "react";
import type { LicenseInfo } from "@/types/admin";
import { activateLicense, getLicense } from "@/services/license.service";
import { StatsGrid } from "@/components/charts/StatsGrid";
import { Button } from "@/components/ui/Button";
import { FormMessage, type FormMessageValue } from "@/components/ui/FormMessage";
import { Panel } from "@/components/ui/Panel";
import { formatDate } from "@/utils/format";

export function LicenseSummary() {
  const [license, setLicense] = useState<LicenseInfo>({});
  const [message, setMessage] = useState<FormMessageValue>();

  async function refresh() {
    setLicense(await getLicense());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function submitLicense(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const key = new FormData(event.currentTarget).get("key")?.toString() || "";

    try {
      await activateLicense(key);
      setMessage({ text: "License activated.", type: "success" });
      event.currentTarget.reset();
      refresh();
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Unable to activate license.", type: "error" });
    }
  }

  return (
    <div className="stack">
      <StatsGrid
        stats={[
          { label: "Plan", value: license.plan || "-", tone: "blue" },
          { label: "Status", value: license.status || "-", tone: "green" },
          { label: "Seats", value: `${license.used_seats || 0}/${license.seats || 0}`, tone: "amber" },
          { label: "Expires", value: formatDate(license.expires_at), tone: "red" }
        ]}
      />
      <Panel title="Activate license">
        <form onSubmit={submitLicense}>
          <div className="field">
            <label>License key</label>
            <input name="key" required />
          </div>
          <Button type="submit" variant="green">
            Activate
          </Button>
          <FormMessage message={message} />
        </form>
      </Panel>
    </div>
  );
}

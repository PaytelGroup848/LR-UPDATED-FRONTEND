import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { LicenseSummary } from "@/components/license/LicenseSummary";

export default function LicensingPage() {
  return (
    <AdminShell>
      <PageHeader title="Licensing" description="View license status, seat usage, and activation details." />
      <LicenseSummary />
    </AdminShell>
  );
}

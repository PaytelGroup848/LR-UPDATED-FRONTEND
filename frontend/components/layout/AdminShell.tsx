import { AdminHeader } from "./AdminHeader";

export function AdminShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <AdminHeader />
      <main>{children}</main>
    </div>
  );
}

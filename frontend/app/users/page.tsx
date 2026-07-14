"use client";

import { useMemo, useState } from "react";
import type { Id, User } from "@/types/admin";
import { AdminShell } from "@/components/layout/AdminShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/tables/DataTable";
import { UserForm, UserImportForm } from "@/components/forms/UserForm";
import { useAdminData } from "@/hooks/useAdminData";
import { bulkDeleteUsers, deleteUser, updateUser } from "@/services/user.service";
import { formatDate } from "@/utils/format";

export default function UsersPage() {
  const { users, loading, refresh } = useAdminData();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [lastLogin, setLastLogin] = useState("all");
  const [selected, setSelected] = useState<Set<Id>>(new Set());

  const filteredUsers = useMemo(() => {
    const now = Date.now();

    return users.filter((user) => {
      const matchesSearch = user.username.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = status === "all" || (status === "active" ? user.is_active !== false : user.is_active === false);
      let matchesLogin = true;

      if (lastLogin === "never") {
        matchesLogin = !user.last_login_at;
      } else if (lastLogin !== "all" && user.last_login_at) {
        const ageDays = (now - new Date(user.last_login_at).getTime()) / 86400000;
        matchesLogin = ageDays <= Number(lastLogin);
      }

      return matchesSearch && matchesStatus && matchesLogin;
    });
  }, [lastLogin, search, status, users]);

  function toggleSelected(user: User) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(user.id)) next.delete(user.id);
      else next.add(user.id);
      return next;
    });
  }

  async function editUser(user: User) {
    const username = window.prompt("Username", user.username);
    if (!username) return;
    const role = window.prompt("Role", user.role || "User") || user.role || "User";
    const statusValue = (window.prompt("Status: active or inactive", user.is_active === false ? "inactive" : "active") || "active").toLowerCase();
    const windowsUsername = window.prompt("Windows/RDP username", user.windows_username || "") || "";
    const windowsDomain = window.prompt("Windows domain", user.windows_domain || "") || "";
    const windowsPassword = window.prompt("New Windows/RDP password (leave blank to keep existing)", "") || "";

    await updateUser(user.id, {
      username,
      role,
      is_active: statusValue !== "inactive",
      windows_username: windowsUsername,
      windows_domain: windowsDomain,
      windows_account_enabled: Boolean(windowsUsername),
      ...(windowsPassword ? { windows_password: windowsPassword } : {})
    });
    refresh();
  }

  async function removeUser(id: Id) {
    if (!window.confirm("Delete this user?")) return;
    await deleteUser(id);
    refresh();
  }

  async function removeBulk() {
    if (!selected.size || !window.confirm("Delete selected users?")) return;
    await bulkDeleteUsers(Array.from(selected));
    setSelected(new Set());
    refresh();
  }

  return (
    <AdminShell>
      <PageHeader title="Users" description="Create, import, search, edit, and delete portal users." action={<Button onClick={refresh}>{loading ? "Refreshing..." : "Refresh"}</Button>} />
      <div className="layout">
        <UserForm onSaved={refresh} />
        <div>
          <div className="toolbar">
            <input placeholder="Search users" value={search} onChange={(event) => setSearch(event.target.value)} />
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="all">All users</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <select value={lastLogin} onChange={(event) => setLastLogin(event.target.value)}>
              <option value="all">Any login</option>
              <option value="never">Never logged in</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
            </select>
            <Button onClick={removeBulk}>Bulk Delete</Button>
          </div>
          <UserImportForm onSaved={refresh} />
          <DataTable
            rows={filteredUsers}
            getKey={(row) => row.id}
            columns={[
              { header: "", cell: (row) => <input checked={selected.has(row.id)} onChange={() => toggleSelected(row)} type="checkbox" /> },
              { header: "Username", cell: (row) => row.username },
              { header: "Role", cell: (row) => row.role || "User" },
              {
                header: "Windows Session",
                cell: (row) => (
                  <Badge value={row.windows_account_configured ? row.windows_username || "configured" : "shared"} />
                )
              },
              { header: "Status", cell: (row) => <Badge value={row.is_active !== false ? "active" : "inactive"} /> },
              { header: "Last login", cell: (row) => formatDate(row.last_login_at) },
              {
                header: "Actions",
                cell: (row) => (
                  <div className="actions">
                    <Button onClick={() => editUser(row)}>Edit</Button>
                    <Button onClick={() => removeUser(row.id)} variant="danger">
                      Delete
                    </Button>
                  </div>
                )
              }
            ]}
          />
        </div>
      </div>
    </AdminShell>
  );
}

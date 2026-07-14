import tkinter as tk
from tkinter import ttk, messagebox

from api_client import ApiError
from dialogs import FormDialog
from resources.styles import SUCCESS, DANGER, button, plain_button


class ServersTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.servers = []
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        button(toolbar, "Add Server", self.add_server, SUCCESS).pack(side=tk.LEFT, padx=5)
        button(toolbar, "Edit", self.edit_server, SUCCESS).pack(side=tk.LEFT, padx=5)
        button(toolbar, "Delete", self.delete_server, DANGER).pack(side=tk.LEFT, padx=5)
        plain_button(toolbar, "Refresh", self.refresh).pack(side=tk.LEFT, padx=5)

        columns = ("id", "name", "host", "username", "port")

        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col.upper())

        self.tree.pack(fill=tk.BOTH, expand=True)

    def refresh(self):
        if not self.app.require_login():
            return
        try:
            servers = self.app.client.servers()
            self.servers = servers if isinstance(servers, list) else []

            self.tree.delete(*self.tree.get_children())

            for s in self.servers:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        s.get("id"),
                        s.get("name"),
                        s.get("host") or s.get("ip_address"),
                        s.get("username") or s.get("windows_username") or "",
                        s.get("port") or s.get("rdp_port"),
                    ),
                )
            self.app.set_status(f"Loaded {len(self.servers)} servers")
        except ApiError as e:
            messagebox.showerror("Servers", str(e))

    def add_server(self):
        dialog = FormDialog(
            self,
            "Add Server",
            [
                {"key": "name", "label": "Name"},
                {"key": "host", "label": "Host/IP"},
                {"key": "username", "label": "Username"},
                {"key": "password", "label": "Password"},
                {"key": "port", "label": "Port"},
            ],
        )

        if not dialog.result:
            return

        try:
            self.app.client.post("/add-server", dialog.result)
            self.refresh()
            messagebox.showinfo("Success", "Server Added")
        except ApiError as e:
            messagebox.showerror("Error", str(e))


    def edit_server(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Edit", "Please select a server")
            return

        values = self.tree.item(selected[0])["values"]

        server_id = values[0]  

        dialog = FormDialog(
            self,
            "Edit Server",
            [
                {"key": "name", "label": "Name", "value": values[1]},
                {"key": "host", "label": "Host/IP", "value": values[2]},
                {"key": "username", "label": "Username", "value": values[3]},
                {"key": "password", "label": "Password"},
                {"key": "port", "label": "Port", "value": values[4]},
            ],
        )

        if not dialog.result:
            return

        try:
            self.app.client.post(f"/update-server/{server_id}", dialog.result)
            self.refresh()
            messagebox.showinfo("Success", "Server Updated")
        except ApiError as e:
            messagebox.showerror("Error", str(e))



    def delete_server(self):
        selected = self.tree.selection()

        if not selected:
            return

        server_id = self.tree.item(selected[0])["values"][0]

        try:
            self.app.client.delete(f"/delete-server/{server_id}")
            self.refresh()
        except ApiError as e:
            messagebox.showerror("Error", str(e))

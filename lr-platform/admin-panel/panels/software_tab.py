import tkinter as tk
from tkinter import messagebox, ttk

from api_client import ApiError
from dialogs import FormDialog
from resources.styles import DANGER, SUCCESS, WARNING, button, plain_button


class SoftwareTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.apps = []
        self.servers = []
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=12, pady=12)
        button(toolbar, 'Add Software', self.add_software, SUCCESS).pack(side=tk.LEFT, padx=(0, 8))
        button(toolbar, 'Edit', self.edit_software, WARNING).pack(side=tk.LEFT, padx=(0, 8))
        button(toolbar, 'Delete', self.delete_software, DANGER).pack(side=tk.LEFT, padx=(0, 8))
        plain_button(toolbar, 'Refresh', self.refresh).pack(side=tk.LEFT)

        columns = ('id', 'name', 'server', 'target', 'active')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')
        widths = {'id': 60, 'name': 190, 'server': 180, 'target': 360, 'active': 80}
        labels = {'id': 'ID', 'name': 'Name', 'server': 'Server', 'target': 'Launch Target', 'active': 'Active'}
        for key in columns:
            self.tree.heading(key, text=labels[key])
            self.tree.column(key, width=widths[key], anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12), side=tk.LEFT)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 12))
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh(self):
        if not self.app.require_login():
            return
        try:
            self.servers = self.app.client.servers()
            self.apps = self.app.client.apps()
            self._fill()
            self.app.on_apps_loaded(self.apps)
            self.app.set_status(f'Loaded {len(self.apps)} software items')
        except ApiError as error:
            messagebox.showerror('Software', str(error))

    def selected_app(self):
        selection = self.tree.selection()
        if not selection:
            return None
        app_id = str(self.tree.item(selection[0], 'values')[0])
        return next((item for item in self.apps if str(item.get('id')) == app_id), None)

    def add_software(self):
        self._save_dialog('Add Software')

    def edit_software(self):
        item = self.selected_app()
        if not item:
            messagebox.showwarning('Software', 'Select software first')
            return
        self._save_dialog('Edit Software', item)

    def delete_software(self):
        item = self.selected_app()
        if not item:
            messagebox.showwarning('Software', 'Select software first')
            return
        if not messagebox.askyesno('Delete Software', f"Delete {item.get('name')}?"):
            return
        try:
            self.app.client.delete_app(item['id'])
            self.refresh()
            messagebox.showinfo('Software', 'Software deleted')
        except ApiError as error:
            messagebox.showerror('Software', str(error))

    def _save_dialog(self, title, item=None):
        if not self.servers:
            try:
                self.servers = self.app.client.servers()
            except ApiError as error:
                messagebox.showerror('Software', str(error))
                return
        if not self.servers:
            messagebox.showwarning('Software', 'No server found. Add an RDP server in backend first.')
            return

        server_labels = [self._server_label(server) for server in self.servers]
        initial = {
            'server': self._server_label(self._server_by_id(item.get('server_id'))) if item else server_labels[0],
            'name': item.get('name', '') if item else '',
            'remote_app_program': item.get('remote_app_program') or '' if item else '',
            'initial_program': item.get('initial_program') or '' if item else '',
            'working_directory': item.get('working_directory') or '' if item else '',
            'arguments': item.get('arguments') or '' if item else '',
            'description': item.get('description') or '' if item else '',
            'is_active': 'true' if not item or item.get('is_active') else 'false',
        }
        dialog = FormDialog(self, title, [
            {'key': 'server', 'label': 'Server', 'values': server_labels},
            {'key': 'name', 'label': 'Software Name'},
            {'key': 'remote_app_program', 'label': 'RemoteApp Alias/Path'},
            {'key': 'initial_program', 'label': 'Initial Program'},
            {'key': 'working_directory', 'label': 'Working Directory'},
            {'key': 'arguments', 'label': 'Arguments'},
            {'key': 'description', 'label': 'Description', 'multiline': True},
            {'key': 'is_active', 'label': 'Active', 'values': ['true', 'false']},
        ], initial)
        if not dialog.result:
            return
        server = self._server_from_label(dialog.result.pop('server'))
        payload = dict(dialog.result)
        payload['server_id'] = server['id']
        remote_app_program = (payload.get('remote_app_program') or '').strip()
        initial_program = (payload.get('initial_program') or '').strip()
        if not remote_app_program and not initial_program:
            messagebox.showwarning('Software', 'Enter RemoteApp Alias/Path or Initial Program')
            return
        payload['display_mode'] = 'remote_app'
        payload['launch_mode'] = 'remote_app' if remote_app_program else 'initial_program'
        try:
            if item:
                self.app.client.update_app(item['id'], payload)
            else:
                self.app.client.create_app(payload)
            self.refresh()
            messagebox.showinfo('Software', 'Software saved')
        except ApiError as error:
            messagebox.showerror('Software', str(error))

    def _fill(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.apps:
            server = item.get('server') or self._server_by_id(item.get('server_id')) or {}
            target = item.get('remote_app_program') or item.get('initial_program') or item.get('target') or '-'
            self.tree.insert('', tk.END, values=(
                item.get('id'),
                item.get('name', ''),
                server.get('name', ''),
                target,
                'Yes' if item.get('is_active') else 'No',
            ))

    def _server_by_id(self, server_id):
        return next((server for server in self.servers if str(server.get('id')) == str(server_id)), None)

    def _server_label(self, server):
        if not server:
            return ''
        return f"{server.get('id')} - {server.get('name')} ({server.get('host') or server.get('ip_address')})"

    def _server_from_label(self, label):
        server_id = str(label).split(' - ', 1)[0]
        return self._server_by_id(server_id) or self.servers[0]

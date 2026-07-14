import ntpath
import platform
import re
import subprocess
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from api_client import ApiError
from resources.styles import DANGER, SUCCESS, button, plain_button


class AssignTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.users = []
        self.apps = []
        self.assigned_ids = set()
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=12, pady=12)
        ttk.Label(top, text='User').pack(side=tk.LEFT)
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(top, textvariable=self.user_var, state='readonly', width=38)
        self.user_combo.pack(side=tk.LEFT, padx=8)
        self.user_combo.bind('<<ComboboxSelected>>', lambda _event: self.load_for_user())
        plain_button(top, 'Refresh', self.refresh).pack(side=tk.LEFT, padx=8)

        lists = ttk.Frame(self)
        lists.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        left = ttk.LabelFrame(lists, text='Assigned Software')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right = ttk.LabelFrame(lists, text='Available Software')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self.assigned_tree = self._tree(left)
        self.available_tree = self._tree(right)

        actions = ttk.Frame(self)
        actions.pack(fill=tk.X, padx=12, pady=(0, 12))
        button(actions, 'Assign Selected', self.assign_selected, SUCCESS).pack(side=tk.LEFT, padx=(0, 8))
        button(actions, 'Remove Selected', self.remove_selected, DANGER).pack(side=tk.LEFT)

    def _tree(self, parent):
        tree = ttk.Treeview(parent, columns=('id', 'name'), show='headings', selectmode='browse')
        tree.heading('id', text='ID')
        tree.heading('name', text='Software')
        tree.column('id', width=60, anchor=tk.W)
        tree.column('name', width=260, anchor=tk.W)
        tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        return tree

    def refresh(self):
        if not self.app.require_login():
            return
        try:
            self.users = self.app.client.users()
            self.apps = self.app.client.apps()
            labels = [self._user_label(user) for user in self.users]
            self.user_combo['values'] = labels
            if labels and not self.user_var.get():
                self.user_var.set(labels[0])
                self.load_for_user()
            else:
                self._fill()
        except ApiError as error:
            messagebox.showerror('Assignments', str(error))

    def update_sources(self, users=None, apps=None):
        if users is not None:
            self.users = users
            self.user_combo['values'] = [self._user_label(user) for user in users]
        if apps is not None:
            self.apps = apps
        self._fill()

    def load_for_user(self):
        user = self.selected_user()
        if not user:
            return
        try:
            data = self.app.client.assignments_for_user(user['id'])
            self.assigned_ids = set(data.get('assigned_app_ids', []))
            self.apps = data.get('available_apps', self.apps)
            self._fill()
        except ApiError as error:
            messagebox.showerror('Assignments', str(error))

    def assign_selected(self):
        user = self.selected_user()
        app_id = self._selected_id(self.available_tree)
        if not user or not app_id:
            messagebox.showwarning('Assignments', 'Select user and software')
            return
        try:
            app = self._app_by_id(app_id)
            self.app.client.assign_app(app_id, user['id'])
            if app:
                self._sync_user_desktop_shortcut('create', user, app)
            self.load_for_user()
            messagebox.showinfo('Assignments', 'Software assigned')
        except ApiError as error:
            messagebox.showerror('Assignments', str(error))

    def remove_selected(self):
        user = self.selected_user()
        app_id = self._selected_id(self.assigned_tree)
        if not user or not app_id:
            messagebox.showwarning('Assignments', 'Select assigned software')
            return
        try:
            app = self._app_by_id(app_id)
            self.app.client.unassign_app(app_id, user['id'])
            if app:
                self._sync_user_desktop_shortcut('delete', user, app)
            self.load_for_user()
            messagebox.showinfo('Assignments', 'Assignment removed')
        except ApiError as error:
            messagebox.showerror('Assignments', str(error))

    def selected_user(self):
        label = self.user_var.get()
        user_id = str(label).split(' - ', 1)[0]
        return next((user for user in self.users if str(user.get('id')) == user_id), None)

    def _selected_id(self, tree):
        selection = tree.selection()
        if not selection:
            return None

        return tree.item(selection[0], 'values')[0]

    def _fill(self):
        self.assigned_tree.delete(*self.assigned_tree.get_children())
        self.available_tree.delete(*self.available_tree.get_children())
        for item in self._software_apps():
            target = self.assigned_tree if item.get('id') in self.assigned_ids else self.available_tree
            target.insert('', tk.END, values=(item.get('id'), item.get('name', '')))

    def _software_apps(self):
        return [
            item for item in self.apps
            if item.get('item_type') != 'folder' and not item.get('folder_path')
        ]

    def _app_by_id(self, app_id):
        return next((item for item in self._software_apps() if str(item.get('id')) == str(app_id)), None)

    def _sync_user_desktop_shortcut(self, action, user, app):
        if platform.system().lower() != 'windows':
            return

        username = self._windows_username(user)
        shortcut_name = self._safe_shortcut_name(app.get('name'))
        target_path = self._app_target(app)
        arguments = str(app.get('arguments') or '').strip()
        working_directory = str(app.get('working_directory') or '').strip()
        if working_directory.lower().endswith(('.exe', '.bat', '.cmd', '.msi')):
            working_directory = ntpath.dirname(working_directory)
        if not working_directory and '\\' in target_path:
            working_directory = ntpath.dirname(target_path)

        if not username:
            raise ApiError('Windows username is missing for selected user')
        if action != 'delete' and not target_path:
            raise ApiError('Application target path is missing')

        result = self._run_shortcut_script(
            action,
            username,
            shortcut_name,
            target_path,
            arguments,
            working_directory,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or 'PowerShell returned an error').strip()
            raise ApiError(f'Application assigned, but desktop shortcut was not created: {message}')

    def _run_shortcut_script(self, action, username, shortcut_name, target_path, arguments, working_directory):
        script = r"""param(
    [string]$action,
    [string]$username,
    [string]$shortcutName,
    [string]$targetPath,
    [string]$arguments,
    [string]$workingDirectory
)
$ErrorActionPreference = 'Stop'
if (-not $username) { throw 'Windows username is required.' }
if (-not $shortcutName) { throw 'Shortcut name is required.' }
$profileDesktop = Join-Path (Join-Path 'C:\Users' $username) 'Desktop'
$shortcutPath = Join-Path $profileDesktop ($shortcutName + '.lnk')
if ($action -eq 'delete') {
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath -Force
    }
    exit 0
}
if (-not $targetPath) { throw 'Shortcut target is required.' }
if (-not (Test-Path -LiteralPath $profileDesktop)) {
    New-Item -ItemType Directory -Path $profileDesktop -Force | Out-Null
}
$targetPath = [Environment]::ExpandEnvironmentVariables($targetPath)
$workingDirectory = [Environment]::ExpandEnvironmentVariables($workingDirectory)
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
if ($arguments) { $shortcut.Arguments = $arguments }
if ($workingDirectory) { $shortcut.WorkingDirectory = $workingDirectory }
if ($targetPath.ToLowerInvariant().EndsWith('.exe') -and (Test-Path -LiteralPath $targetPath)) {
    $shortcut.IconLocation = $targetPath
}
$shortcut.Save()
if (Test-Path -LiteralPath $targetPath) {
    $aclPath = if ((Get-Item -LiteralPath $targetPath).PSIsContainer) { $targetPath } else { Split-Path -Parent $targetPath }
    if ($aclPath) {
        & icacls $aclPath /grant "$username`:(OI)(CI)RX" /T /C | Out-Null
    }
}
exit 0
"""
        script_path = None
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False, encoding='utf-8') as handle:
                handle.write(script)
                script_path = handle.name
            return subprocess.run(
                [
                    'powershell',
                    '-NoProfile',
                    '-NonInteractive',
                    '-ExecutionPolicy',
                    'Bypass',
                    '-File',
                    script_path,
                    action,
                    username,
                    shortcut_name,
                    target_path,
                    arguments,
                    working_directory,
                ],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
        finally:
            if script_path:
                try:
                    Path(script_path).unlink(missing_ok=True)
                except OSError:
                    pass

    def _app_target(self, app):
        return str(
            app.get('target')
            or app.get('initial_program')
            or app.get('remote_app_program')
            or ''
        ).strip()

    def _windows_username(self, user):
        value = str((user or {}).get('windows_username') or (user or {}).get('username') or '').strip()
        if '\\' in value:
            value = value.rsplit('\\', 1)[-1]
        if '@' in value:
            value = value.split('@', 1)[0]
        return value

    def _safe_shortcut_name(self, value):
        name = re.sub(r'[\\/:*?"<>|]+', ' ', str(value or '').strip())
        return re.sub(r'\s+', ' ', name).strip() or 'Application'

    def _user_label(self, user):
        return f"{user.get('id')} - {user.get('username')}"

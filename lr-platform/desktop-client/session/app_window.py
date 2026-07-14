import webbrowser
import os
import re
import tempfile
from tkinter import BOTH, LEFT, X, Button, Frame, Label, filedialog


class AppWindowMixin:
    def show_apps(self, apps):
        self.clear()

        frame = Frame(self.root, padx=24, pady=24)
        frame.pack(fill=BOTH, expand=True)

        top = Frame(frame)
        top.pack(fill=X, pady=(0, 18))

        Label(top, text='My Applications', font=('Segoe UI', 18, 'bold')).pack(side=LEFT)
        Button(top, text='Logout', command=self.show_login).pack(side='right')

        self.app_frame = Frame(frame)
        self.app_frame.pack(fill=BOTH, expand=True)

        if not apps:
            Label(self.app_frame, text='No applications assigned yet.').pack(anchor='w')
            return

        for app in apps:
            Button(
                self.app_frame,
                text=app.get('name', 'Application'),
                command=lambda item=app: self.launch_app(item),
                height=2,
            ).pack(fill=X, pady=6)

        tools = Frame(frame)
        tools.pack(fill=X, pady=(12, 0))

        Button(tools, text='Upload File', command=self.upload_file).pack(fill=X, pady=3)
        Button(tools, text='Clipboard', command=self.show_clipboard).pack(fill=X, pady=3)
        Button(tools, text='New Ticket', command=self.show_ticket).pack(fill=X, pady=3)

        self.status = Label(frame, text='', fg='#666')
        self.status.pack(anchor='w', pady=(12, 0))

    def launch_app(self, app):
        self.status.config(text=f"Starting {app.get('name', 'application')}...")
        self.run_async(lambda: self._launch_app(app))

    def _launch_app(self, app):
        view_mode = "remote_app"
        if getattr(self, "view_mode_var", None):
            view_mode = self.view_mode_var.get() or view_mode

        result = self.api.post_json(f"/portal/api/apps/{app['id']}/launch", {"view_mode": view_mode})
        launch_url = result.get('launch_url') or result.get('client_url')
        rdp_file_url = result.get('rdp_file_url')

        if launch_url:
            webbrowser.open(launch_url)
            self.root.after(0, lambda: self.status.config(text='Remote app opened.'))
            return

        if rdp_file_url:
            path = self._download_rdp_file(rdp_file_url, app)
            os.startfile(path)
            self.root.after(0, lambda: self.status.config(text='RDP file opened.'))
            return

        raise RuntimeError(result.get('warning') or result.get('message') or 'Launch URL was not returned by the server.')

    def _download_rdp_file(self, url, app):
        content, headers = self.api.get_bytes(url)
        filename = self._rdp_filename(headers, app)
        path = os.path.join(tempfile.gettempdir(), filename)

        with open(path, 'wb') as handle:
            handle.write(content)

        return path

    def _rdp_filename(self, headers, app):
        disposition = headers.get('Content-Disposition', '') if headers else ''
        match = re.search(r'filename="?([^";]+)"?', disposition)
        if match:
            return self._safe_filename(match.group(1))

        app_name = app.get('name') or 'lr-remote'
        return self._safe_filename(f'{app_name}.rdp')

    def _safe_filename(self, filename):
        filename = re.sub(r'[^A-Za-z0-9._-]+', '_', filename).strip('._')
        if not filename.lower().endswith('.rdp'):
            filename = f'{filename}.rdp'
        return filename or 'lr-remote.rdp'

    def upload_file(self):
        file_path = filedialog.askopenfilename()

        if not file_path:
            return

        self.status.config(text='Uploading file...')
        self.run_async(lambda: self._upload_file(file_path))

    def _upload_file(self, file_path):
        self.api.post_file('/api/transfers', file_path)
        self.root.after(0, lambda: self.status.config(text='File uploaded.'))

    def reload_apps(self):
        self.run_async(self._reload_apps)

    def _reload_apps(self):
        apps = self.api.get_json('/portal/api/apps').get('apps', [])
        self.root.after(0, lambda: self.show_apps(apps))

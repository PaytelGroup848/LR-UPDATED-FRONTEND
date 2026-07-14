import tkinter as tk
from tkinter import messagebox, ttk

from api_client import ApiError
from resources.styles import DANGER, PRIMARY, SUCCESS, button


class SettingsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        form = ttk.Frame(self, padding=18)
        form.pack(fill=tk.X)

        ttk.Label(form, text='Backend URL').grid(row=0, column=0, sticky=tk.W, pady=8)
        self.backend_url = tk.StringVar(value=self.app.settings.get('backend_url', self.app.client.base_url))
        ttk.Entry(form, textvariable=self.backend_url, width=58).grid(row=0, column=1, sticky=tk.W, padx=12, pady=8)

        ttk.Label(form, text='Admin Username').grid(row=1, column=0, sticky=tk.W, pady=8)
        self.username = tk.StringVar(value=self.app.settings.get('username', ''))
        ttk.Entry(form, textvariable=self.username, width=32).grid(row=1, column=1, sticky=tk.W, padx=12, pady=8)

        ttk.Label(form, text='Admin Password').grid(row=2, column=0, sticky=tk.W, pady=8)
        self.password = tk.StringVar()
        ttk.Entry(form, textvariable=self.password, show='*', width=32).grid(row=2, column=1, sticky=tk.W, padx=12, pady=8)

        actions = ttk.Frame(form)
        actions.grid(row=3, column=1, sticky=tk.W, padx=12, pady=14)
        button(actions, 'Save Settings', self.save, SUCCESS).pack(side=tk.LEFT, padx=(0, 8))
        button(actions, 'Login', self.login, PRIMARY).pack(side=tk.LEFT, padx=(0, 8))
        button(actions, 'Logout', self.logout, DANGER).pack(side=tk.LEFT, padx=(0, 8))
        button(actions, 'Test Backend', self.test_backend, PRIMARY).pack(side=tk.LEFT)

    def save(self):
        self.app.settings['backend_url'] = self.backend_url.get().strip()
        self.app.settings['username'] = self.username.get().strip()
        self.app.store.save(self.app.settings)
        self.app.client.set_base_url(self.app.settings['backend_url'])
        self.app.set_status('Settings saved')
        messagebox.showinfo('Settings', 'Settings saved')

    def login(self):
        self.save()
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            messagebox.showwarning('Login', 'Enter admin username and password')
            return
        try:
            self.app.client.login(username, password)
            self.app.set_logged_in(True, username)
            self.app.refresh_all()
            messagebox.showinfo('Login', 'Login successful')
        except ApiError as error:
            self.app.set_logged_in(False)
            messagebox.showerror('Login', str(error))

    def logout(self):
        self.app.logout()
        self.password.set('')
        messagebox.showinfo('Logout', 'Logged out successfully')

    def test_backend(self):
        self.save()
        try:
            data = self.app.client.health()
            health = data.get('health', {})
            messagebox.showinfo('Backend', f"Connected\nStatus: {data.get('status')}\nCPU: {health.get('cpu_percent', 0)}%")
        except ApiError as error:
            messagebox.showerror('Backend', str(error))

import tkinter as tk
from tkinter import messagebox, ttk

from api_client import ApiError
from resources.styles import PRIMARY, button, plain_button


class UrlsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.users = []
        self._build()

    def _build(self):
        form = ttk.Frame(self, padding=16)
        form.pack(fill=tk.X)

        ttk.Label(form, text='User').grid(row=0, column=0, sticky=tk.W, pady=6)
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(form, textvariable=self.user_var, state='readonly', width=42)
        self.user_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=6)

        ttk.Label(form, text='Expires Minutes').grid(row=1, column=0, sticky=tk.W, pady=6)
        self.expiry_var = tk.StringVar(value='60')
        ttk.Entry(form, textvariable=self.expiry_var, width=12).grid(row=1, column=1, sticky=tk.W, padx=10, pady=6)

        self.one_time = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text='One time link', variable=self.one_time).grid(row=2, column=1, sticky=tk.W, padx=10, pady=6)

        actions = ttk.Frame(form)
        actions.grid(row=3, column=1, sticky=tk.W, padx=10, pady=12)
        button(actions, 'Generate URL', self.generate, PRIMARY).pack(side=tk.LEFT, padx=(0, 8))
        plain_button(actions, 'Copy', self.copy).pack(side=tk.LEFT)

        self.output = tk.Text(self, height=8, wrap=tk.WORD, font=('Segoe UI', 10))
        self.output.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

    def update_users(self, users):
        self.users = users or []
        self.user_combo['values'] = [self._user_label(user) for user in self.users]
        if self.users and not self.user_var.get():
            self.user_combo.current(0)

    def refresh(self):
        if not self.app.require_login():
            return
        try:
            self.update_users(self.app.client.users())
        except ApiError as error:
            messagebox.showerror('URLs', str(error))

    def generate(self):
        user = self.selected_user()
        if not user:
            messagebox.showwarning('URLs', 'Select a user before generating a direct login URL')
            return
        try:
            expires = max(1, int(self.expiry_var.get()))
        except ValueError:
            messagebox.showwarning('URLs', 'Expires minutes must be a number')
            return
        try:
            data = self.app.client.generate_url(user.get('id') if user else None, expires, self.one_time.get())
            url = data.get('url', '')
            download_url = data.get('download_url', '')

            self.output.delete('1.0', tk.END)
            self.output.insert(
                '1.0',
                f'Access URL:\n{url}\n\n'
                f'Download Desktop App:\n{download_url}\n\n'
                f'Expires in: {expires} minutes\n'
                f'User: {user.get("username")}'
            )
        except ApiError as error:
            messagebox.showerror('URLs', str(error))

    def copy(self):
        value = self.output.get('1.0', tk.END).strip()
        if value:
            self.clipboard_clear()
            self.clipboard_append(value)
            messagebox.showinfo('URLs', 'Copied to clipboard')

    def selected_user(self):
        label = self.user_var.get()
        user_id = str(label).split(' - ', 1)[0]
        return next((user for user in self.users if str(user.get('id')) == user_id), None)

    def _user_label(self, user):
        return f"{user.get('id')} - {user.get('username')}"

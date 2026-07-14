import sys
import os
import shutil
import subprocess
import tkinter as tk
import threading

from PIL import Image, ImageTk
from tkinter import messagebox, ttk

from api_client import ApiClient, ApiError
from config import APP_ID, APP_NAME, APP_VERSION, DEFAULT_BACKEND_URL, SettingsStore
from dialogs import LicenseLoginDialog
from license_manager_window import LicenseManagerWindow
from panels.assign_folder_tab import AssignFolderTab
from panels.assign_tab import AssignTab
from panels.monitor_tab import MonitorTab
from panels.servers_tab import ServersTab
from panels.settings_tab import SettingsTab
from panels.software_tab import SoftwareTab
from panels.urls_tab import UrlsTab
from panels.users_tab import UsersTab
from resources.styles import BORDER, HEADER_BG, MUTED, PRIMARY, SUCCESS, SURFACE, TEXT, apply_style, button, resource_path
from update_client import check_for_update, prompt_and_launch_update

UPDATE_CHECK_INTERVAL_MS = 10 * 60 * 1000

class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title('LR Admin Panel')
        self.root.geometry('1180x760')
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.client = ApiClient(self.settings.get('backend_url', DEFAULT_BACKEND_URL))
        self.logged_in = False
        self._update_check_running = False

        apply_style(root)
        self.root.minsize(1040, 680)
        self._build()
        self.root.after(2500, self.check_for_updates_silent)

    def _load_logo(self):
        logo_path = resource_path('lr-remote-logo.png')
        if not logo_path.exists():
            return None

        try:
            image = Image.open(logo_path)
        except (OSError, tk.TclError):
            return None

        if image.width > 230:
            height = max(1, int(image.height * (230 / image.width)))
            image = image.resize((230, height), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(image)

    def _build(self):
        header = tk.Frame(self.root, bg=HEADER_BG, height=82, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=HEADER_BG)
        brand.pack(side=tk.LEFT, padx=20, pady=13)

        self.logo_image = self._load_logo()
        if self.logo_image:
            tk.Label(brand, image=self.logo_image, bg=HEADER_BG, borderwidth=0).pack(side=tk.LEFT, padx=(0, 14))
        else:
            ttk.Label(brand, text='LR Remote Access', style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 14))

        title_stack = tk.Frame(brand, bg=HEADER_BG)
        title_stack.pack(side=tk.LEFT)
        tk.Label(title_stack, text='Admin Panel', bg=HEADER_BG, fg=TEXT, font=('Segoe UI', 18, 'bold')).pack(anchor=tk.W)
        tk.Label(title_stack, text='Manage users, servers, software and licenses', bg=HEADER_BG, fg=MUTED, font=('Segoe UI', 9)).pack(anchor=tk.W)

        self.license_button = button(header, 'Licence Manage', self.open_license_manager, PRIMARY)
        self.license_button.pack(side=tk.RIGHT, padx=(0, 18))

        self.update_button = button(header, 'Check Update', self.check_for_updates_manual, SUCCESS)
        self.update_button.pack(side=tk.RIGHT, padx=(0, 8))

        self.login_label = tk.Label(header, text='Not logged in', bg=HEADER_BG, fg=MUTED, font=('Segoe UI', 10, 'bold'))
        self.login_label.pack(side=tk.RIGHT, padx=18)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=18, pady=(16, 14))

        self.users_tab = UsersTab(self.notebook, self)
        self.servers_tab = ServersTab(self.notebook, self)
        self.software_tab = SoftwareTab(self.notebook, self)
        self.assign_tab = AssignTab(self.notebook, self)
        self.assign_folder_tab = AssignFolderTab(self.notebook, self)
        self.urls_tab = UrlsTab(self.notebook, self)
        self.monitor_tab = MonitorTab(self.notebook, self)
        self.settings_tab = SettingsTab(self.notebook, self)

        self.notebook.add(self.users_tab, text='Users')
        self.notebook.add(self.servers_tab, text='Servers')
        self.notebook.add(self.software_tab, text='Software')
        self.notebook.add(self.assign_tab, text='Assign')
        self.notebook.add(self.assign_folder_tab, text='Assign Folder')
        self.notebook.add(self.urls_tab, text='URLs')
        self.notebook.add(self.monitor_tab, text='Monitor')
        self.notebook.add(self.settings_tab, text='Settings')
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

        footer = tk.Frame(self.root, bg=SURFACE, height=34, highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill=tk.X)
        self.status_label = tk.Label(footer, text='Ready', bg=SURFACE, fg=TEXT, anchor=tk.W, font=('Segoe UI', 9))
        self.status_label.pack(fill=tk.X, padx=12, pady=5)

    def set_status(self, text):
        self.status_label.config(text=text)

    def _backend_url(self):
        return self.settings.get('backend_url') or DEFAULT_BACKEND_URL

    def check_for_updates_silent(self):
        self._check_for_updates(show_no_update=False)

    def check_for_updates_manual(self):
        self._check_for_updates(show_no_update=True)

    def _check_for_updates(self, show_no_update=False):
        if self._update_check_running:
            return

        self._update_check_running = True
        if show_no_update:
            self.set_status('Checking for updates...')

        def worker():
            try:
                info = check_for_update(self._backend_url(), APP_ID, APP_VERSION)
            except Exception as error:
                self.root.after(0, lambda: self._finish_update_check(None, error, show_no_update))
                return

            self.root.after(0, lambda: self._finish_update_check(info, None, show_no_update))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_update_check(self, info, error, show_no_update):
        self._update_check_running = False
        if error:
            if show_no_update:
                self.set_status('Update check failed')
                messagebox.showerror(APP_NAME, f'Update check failed: {error}')
            self._schedule_next_update_check()
            return

        if info:
            self.set_status('Update available')
            if not prompt_and_launch_update(self.root, info, APP_NAME):
                self._schedule_next_update_check()
            return

        if show_no_update:
            self.set_status('Already up to date')
            messagebox.showinfo(APP_NAME, 'Already up to date.')
        self._schedule_next_update_check()

    def _schedule_next_update_check(self):
        self.root.after(UPDATE_CHECK_INTERVAL_MS, self.check_for_updates_silent)

    def set_logged_in(self, value, username=''):
        self.logged_in = value
        self.login_label.config(fg=SUCCESS if value else MUTED)
        self.login_label.config(text=f'Logged in: {username}' if value else 'Not logged in')

    def require_login(self):
        if self.logged_in:
            return True
        messagebox.showwarning('Login Required', 'Open Settings tab and login as an Admin first.')
        self.notebook.select(self.settings_tab)
        return False

    def open_license_manager(self):
        dialog = LicenseLoginDialog(self.root, self)
        if dialog.result and dialog.client:
            window = LicenseManagerWindow(self.root, dialog.client)
            window.focus_set()

    def logout(self):
        try:
            self.client.logout()
        except ApiError:
            pass
        self.set_logged_in(False)
        self.set_status('Logged out')

    def refresh_all(self):
        for tab in (
            self.servers_tab,
            self.users_tab,
            self.software_tab,
            self.assign_tab,
            self.assign_folder_tab,
            self.urls_tab,
            self.monitor_tab,
        ):
            self._refresh_tab(tab)

    def _refresh_tab(self, tab):
        try:
            tab.refresh()
        except Exception as error:
            self.set_status(f'{tab.__class__.__name__} refresh failed: {error}')

    def on_tab_changed(self, _event=None):
        if not self.logged_in:
            return
        selected = self.notebook.nametowidget(self.notebook.select())
        if selected is not self.settings_tab:
            self._refresh_tab(selected)

    def on_users_loaded(self, users):
        self.assign_tab.update_sources(users=users)
        self.assign_folder_tab.update_sources(users=users)
        self.urls_tab.update_users(users)

    def on_apps_loaded(self, apps):
        self.assign_tab.update_sources(apps=apps)
        self.assign_folder_tab.update_sources(apps=apps)







def main():
    root = tk.Tk()
    AdminPanel(root)
    root.mainloop()


if __name__ == '__main__':
    import platform

    if (
        platform.system() == "Windows"
        or os.environ.get('DISPLAY')
        or os.environ.get('LR_ADMIN_XVFB')
    ):
        main()
    else:
        xvfb_run = shutil.which('xvfb-run')
        if xvfb_run:
            env = os.environ.copy()
            env['LR_ADMIN_XVFB'] = '1'
            raise SystemExit(
                subprocess.call(
                    [xvfb_run, '-a', sys.executable, os.path.abspath(__file__)],
                    env=env
                )
            )

        raise SystemExit(
            'LR Admin Panel is a Tkinter desktop app, but no display is available.\n'
            'Install Xvfb, then run this command again:\n'
            '  sudo apt-get update && sudo apt-get install -y xvfb\n'
            'Or run it from a desktop/VNC session with DISPLAY set.'
        )

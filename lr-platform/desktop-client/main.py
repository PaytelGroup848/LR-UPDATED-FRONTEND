import os
import sys
import threading
import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox
from typing import Any

from config import APP_ID, APP_NAME, APP_VERSION, DEFAULT_SERVER_URL
from launcher.login_window import LoginWindowMixin
from session.app_window import AppWindowMixin
from session.async_runner import AsyncRunnerMixin
from session.clipboard_window import ClipboardWindowMixin
from session.ticket_window import TicketWindowMixin
from update_client import check_for_update, prompt_and_launch_update

UPDATE_CHECK_INTERVAL_MS = 10 * 60 * 1000


def create_desktop_shortcut():
    try:
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        shortcut_path = os.path.join(desktop, "LR Remote Access.lnk")

        if os.path.exists(shortcut_path):
            return

        from win32com.client import Dispatch

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.WorkingDirectory = os.path.dirname(sys.executable)
        shortcut.IconLocation = sys.executable
        shortcut.save()

    except Exception as e:
        print("Shortcut error:", e)


def resource_path(filename):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / "resources" / filename


class LRRemoteAccessClient(
    LoginWindowMixin,
    AppWindowMixin,
    ClipboardWindowMixin,
    TicketWindowMixin,
    AsyncRunnerMixin,
):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("LR Remote Access")
        icon_path = resource_path("lr-remote-logo.ico")
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass
        self.root.geometry("760x520")
        self.root.minsize(720, 500)
        self.root.configure(fg_color="#eef5ff")
        self.root.attributes("-topmost", True)

        self.api: Any = None
        self.server_entry: Any = None
        self.username_entry: Any = None
        self.password_entry: Any = None
        self.two_factor_entry: Any = None
        self.view_mode_var: Any = None
        self.ticket_title_entry: Any = None
        self.ticket_description: Any = None
        self.clipboard_text: Any = None
        self.app_frame: Any = None
        self.status: Any = None
        self._update_check_running = False

        self.show_login()
        self.root.after(2500, self.check_for_updates_silent)

    def clear(self):
        for child in self.root.winfo_children():
            child.destroy()

    def run(self):
        self.root.mainloop()

    def _server_url(self):
        if self.server_entry:
            value = self.server_entry.get().strip()
            if value:
                return value
        return DEFAULT_SERVER_URL

    def check_for_updates_silent(self):
        self._check_for_updates(show_no_update=False)

    def _check_for_updates(self, show_no_update=False):
        if self._update_check_running:
            return

        self._update_check_running = True

        def worker():
            try:
                info = check_for_update(self._server_url(), APP_ID, APP_VERSION)
            except Exception as error:
                self.root.after(0, lambda: self._finish_update_check(None, error, show_no_update))
                return

            self.root.after(0, lambda: self._finish_update_check(info, None, show_no_update))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_update_check(self, info, error, show_no_update):
        self._update_check_running = False
        if error:
            if show_no_update:
                messagebox.showerror(APP_NAME, f"Update check failed: {error}")
            self._schedule_next_update_check()
            return

        if info:
            if not prompt_and_launch_update(self.root, info, APP_NAME):
                self._schedule_next_update_check()
            return

        self._schedule_next_update_check()

    def _schedule_next_update_check(self):
        self.root.after(UPDATE_CHECK_INTERVAL_MS, self.check_for_updates_silent)


if __name__ == "__main__":
    create_desktop_shortcut()
    LRRemoteAccessClient().run()

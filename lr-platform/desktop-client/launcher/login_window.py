import sys
from pathlib import Path
from tkinter import messagebox
from typing import Any, Callable, TYPE_CHECKING

import customtkinter as ctk
from PIL import Image

from config import DEFAULT_SERVER_URL
from session.api_client import LRApi


class LoginWindowMixin:
    if TYPE_CHECKING:
        root: Any
        api: LRApi
        status: Any
        logo_image: Any
        server_entry: Any
        username_entry: Any
        password_entry: Any
        two_factor_entry: Any
        remember_me: Any
        view_mode_var: Any

        def clear(self) -> None: ...
        def run_async(self, target: Callable[[], Any]) -> None: ...
        def show_apps(self, apps: list[dict[str, Any]]) -> None: ...

    def _resource_path(self, filename):
        base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        return base_path / "resources" / filename

    def _load_logo_image(self, size=(220, 60)):
        logo_path = self._resource_path("lr-remote-logo.png")
        if not logo_path.exists():
            return None

        image = Image.open(logo_path)
        return ctk.CTkImage(light_image=image, dark_image=image, size=size)

    def show_login(self):
        self.clear()
        self.root.geometry("760x520")
        self.root.configure(fg_color="#eef5ff")

        left_panel = ctk.CTkFrame(
            self.root,
            width=310,
            height=460,
            corner_radius=26,
            fg_color="#ffffff",
            border_width=1,
            border_color="#dbeafe"
        )
        left_panel.place(relx=0.27, rely=0.5, anchor="center")

        self.logo_image = self._load_logo_image()
        if self.logo_image:
            ctk.CTkLabel(
                left_panel,
                image=self.logo_image,
                text=""
            ).pack(pady=(78, 24))
        else:
            ctk.CTkLabel(
                left_panel,
                text="LR",
                font=("Segoe UI", 54, "bold"),
                text_color="#05a85c"
            ).pack(pady=(78, 24))

        ctk.CTkLabel(
            left_panel,
            text="Remote Access",
            font=("Segoe UI", 24, "bold"),
            text_color="#0f172a",
            justify="center"
        ).pack()

        ctk.CTkLabel(
            left_panel,
            text="Secure access to your\nassigned applications",
            font=("Segoe UI", 14),
            text_color="#475569",
            justify="center"
        ).pack(pady=(18, 0))

        card = ctk.CTkFrame(
            self.root,
            width=390,
            height=460,
            corner_radius=26,
            fg_color="#ffffff",
            border_width=1,
            border_color="#dbeafe"
        )
        card.place(relx=0.70, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text="Welcome Back!",
            font=("Segoe UI", 24, "bold"),
            text_color="#0f172a"
        ).pack(anchor="w", padx=34, pady=(34, 4))

        ctk.CTkLabel(
            card,
            text="Login to continue to your dashboard",
            font=("Segoe UI", 13),
            text_color="#64748b"
        ).pack(anchor="w", padx=34, pady=(0, 22))

        self.server_entry = ctk.CTkEntry(
            card,
            placeholder_text="Server URL",
            width=320,
            height=42,
            corner_radius=10,
            border_color="#cbd5e1"
        )
        self.server_entry.insert(0, DEFAULT_SERVER_URL)
        self.server_entry.pack(pady=7)

        self.username_entry = ctk.CTkEntry(
            card,
            placeholder_text="Enter your username",
            width=320,
            height=42,
            corner_radius=10,
            border_color="#cbd5e1"
        )
        self.username_entry.pack(pady=7)

        self.password_entry = ctk.CTkEntry(
            card,
            placeholder_text="Enter your password",
            show="*",
            width=320,
            height=42,
            corner_radius=10,
            border_color="#cbd5e1"
        )
        self.password_entry.pack(pady=7)

        self.two_factor_entry = ctk.CTkEntry(
            card,
            placeholder_text="Enter 2FA code",
            width=320,
            height=42,
            corner_radius=10,
            border_color="#cbd5e1"
        )
        self.two_factor_entry.pack(pady=7)

        self.view_mode_var = ctk.StringVar(value="remote_app")
        view_frame = ctk.CTkSegmentedButton(
            card,
            values=["Remote App View", "Desktop View", "Web View"],
            command=self._set_view_mode,
            width=320,
            height=38,
        )
        view_frame.set("Remote App View")
        view_frame.pack(pady=(8, 4))

        self.remember_me = ctk.CTkCheckBox(
            card,
            text="Remember me",
            font=("Segoe UI", 12),
            text_color="#334155"
        )
        self.remember_me.pack(anchor="w", padx=34, pady=(10, 10))

        ctk.CTkButton(
            card,
            text="Login",
            command=self.login,
            width=320,
            height=46,
            corner_radius=12,
            font=("Segoe UI", 15, "bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="#ffffff"
        ).pack(pady=(4, 14))

        self.status = ctk.CTkLabel(
            card,
            text="Ready to connect",
            font=("Segoe UI", 12),
            text_color="#22c55e"
        )
        self.status.pack(anchor="w", padx=34)

    def login(self):
        base_url = self.server_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        token = self.two_factor_entry.get().strip()

        if not base_url or not username or not password:
            messagebox.showerror(
                "LR Remote Access",
                "Server URL, username, and password are required."
            )
            return

        self.status.configure(text="Signing in...", text_color="#2563eb")
        self.api = LRApi(base_url)
        self.run_async(lambda: self._login(username, password, token))

    def _set_view_mode(self, value):
        modes = {
            "Desktop View": "remote_app",
            "Web View": "html5",
        }
        self.view_mode_var.set(modes.get(value, "remote_app"))

    def _login(self, username, password, token):
        payload = {"username": username, "password": password}

        if token:
            payload["token"] = token

        try:
            self.api.post_json("/login", payload)
            apps = self.api.get_json("/portal/api/apps").get("apps", [])

        except RuntimeError as error:
            message = str(error)

            if "Connection refused" in message or "actively refused" in message:
                message = (
                    f"{message}\n\n"
                    "Check that the gateway service is running and use your "
                    "configured LR_SERVER_URL as the Server URL."
                )

            elif "Not Found" in message or "404" in message:
                message = (
                    f"{message}\n\n"
                    "Use the gateway URL, not an individual microservice URL. "
                    "Set LR_SERVER_URL to your production gateway URL."
                )

            raise RuntimeError(message)

        self.root.after(0, lambda: self.show_apps(apps))

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from api_client import ApiError
from resources.styles import BG, BORDER, DANGER, MUTED, PRIMARY, SUCCESS, SURFACE, TEXT, WARNING, button, plain_button


AUTO_REFRESH_MS = 15000


class MonitorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.auto_refresh = tk.BooleanVar(value=False)
        self.search_text = tk.StringVar()
        self.filter_text = tk.StringVar(value="All")
        self.metric_labels = {}
        self.service_labels = {}
        self._auto_job = None
        self._last_payload = {
            "monitoring": {},
            "sessions": [],
            "agents": [],
            "streams": [],
            "alerts": [],
            "events": [],
        }
        self._build()

    def _build(self):
        self.configure(style="TFrame")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=12, pady=12)
        button(toolbar, "Refresh", self.refresh, PRIMARY).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Checkbutton(
            toolbar,
            text="Auto Refresh",
            variable=self.auto_refresh,
            command=self._toggle_auto_refresh,
        ).pack(side=tk.LEFT, padx=(0, 18))

        ttk.Label(toolbar, text="Search").pack(side=tk.LEFT, padx=(0, 6))
        search = ttk.Entry(toolbar, textvariable=self.search_text, width=28)
        search.pack(side=tk.LEFT, padx=(0, 12))
        search.bind("<KeyRelease>", lambda _event: self._render_tables())

        ttk.Label(toolbar, text="Filter").pack(side=tk.LEFT, padx=(0, 6))
        filter_box = ttk.Combobox(
            toolbar,
            textvariable=self.filter_text,
            values=("All", "Online", "Offline", "Active", "Warning", "Error"),
            state="readonly",
            width=14,
        )
        filter_box.pack(side=tk.LEFT)
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self._render_tables())

        self.last_checked = ttk.Label(toolbar, text="Not refreshed yet", foreground=MUTED)
        self.last_checked.pack(side=tk.RIGHT)

        self._build_metrics()

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.sessions = self._tree(left, "Active Sessions", ("user", "target", "mode", "status", "duration"), {
            "user": ("User", 120),
            "target": ("Target", 180),
            "mode": ("Mode", 110),
            "status": ("Status", 90),
            "duration": ("Duration", 90),
        }, height=7)

        self.agents = self._tree(left, "Agents", ("agent", "host", "status", "last_seen"), {
            "agent": ("Agent ID", 180),
            "host": ("Host", 160),
            "status": ("Status", 90),
            "last_seen": ("Last Seen", 170),
        }, height=7)

        self.streams = self._tree(left, "Streams", ("agent", "active", "viewers", "last_frame"), {
            "agent": ("Agent", 180),
            "active": ("Active", 80),
            "viewers": ("Viewers", 80),
            "last_frame": ("Last Frame", 170),
        }, height=6)

        self.alerts = self._tree(right, "Alerts", ("level", "message", "time"), {
            "level": ("Level", 80),
            "message": ("Message", 260),
            "time": ("Time", 130),
        }, height=8)

        self.events = self._tree(right, "Live Event Log", ("time", "action", "user", "result"), {
            "time": ("Time", 130),
            "action": ("Action", 180),
            "user": ("User", 90),
            "result": ("Result", 80),
        }, height=13)

        self._build_services()

    def _build_metrics(self):
        row = ttk.Frame(self)
        row.pack(fill=tk.X, padx=12, pady=(0, 12))
        for index, key in enumerate(("CPU", "RAM", "Disk", "Network", "Online Agents", "Active Sessions")):
            row.columnconfigure(index, weight=1)
            card = tk.Frame(row, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 6, 0 if index == 5 else 6))
            tk.Label(card, text=key, bg=SURFACE, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, padx=12, pady=(10, 2))
            value = tk.Label(card, text="-", bg=SURFACE, fg=TEXT, font=("Segoe UI", 16, "bold"))
            value.pack(anchor=tk.W, padx=12, pady=(0, 10))
            self.metric_labels[key] = value

    def _build_services(self):
        frame = ttk.LabelFrame(self, text="Backend Status | Database | Guacamole | API | License Server")
        frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        inner = tk.Frame(frame, bg=BG)
        inner.pack(fill=tk.X, padx=10, pady=10)
        for key in ("backend", "database", "guacamole", "api", "license"):
            label = tk.Label(
                inner,
                text=f"{self._service_title(key)}: -",
                bg="#edf5f1",
                fg=TEXT,
                padx=12,
                pady=7,
                font=("Segoe UI", 9, "bold"),
            )
            label.pack(side=tk.LEFT, padx=(0, 8))
            self.service_labels[key] = label

    def _tree(self, parent, title, columns, meta, height):
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        for key in columns:
            label, width = meta[key]
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor=tk.W, stretch=True)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=8)
        return tree

    def refresh(self):
        if not self.app.require_login():
            self._schedule_auto_refresh()
            return

        try:
            monitoring = self.app.client.monitoring()
            sessions = self._items(self.app.client.sessions(), "sessions")
            agents = self._items(self.app.client.agents(), "agents")
            streams = self._items(self.app.client.streams(), "streams")
            alerts = self._items(self.app.client.error_logs(50), "errors")
            events = self._items(self.app.client.logs(80), "logs")
            self._last_payload = {
                "monitoring": monitoring if isinstance(monitoring, dict) else {},
                "sessions": sessions,
                "agents": agents,
                "streams": streams,
                "alerts": alerts,
                "events": events,
            }
            self._render_all()
            self.app.set_status("Monitor refreshed")
        except ApiError as error:
            messagebox.showerror("Monitor", str(error))
        finally:
            self._schedule_auto_refresh()

    def _render_all(self):
        monitoring = self._last_payload["monitoring"]
        self._fill_metrics(monitoring)
        self._render_tables()
        self._fill_services(monitoring)
        self.last_checked.config(text=f"Last checked: {datetime.now().strftime('%H:%M:%S')}")

    def _render_tables(self):
        sessions = self._filter_items(self._last_payload["sessions"])
        agents = self._filter_items(self._last_payload["agents"])
        streams = self._filter_items(self._last_payload["streams"])
        alerts = self._filter_items(self._last_payload["alerts"])
        events = self._filter_items(self._last_payload["events"])
        self._fill_sessions(sessions)
        self._fill_agents(agents)
        self._fill_streams(streams)
        self._fill_alerts(alerts)
        self._fill_events(events)

    def _items(self, value, key=None):
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            candidates = [value.get(key)] if key else []
            candidates.extend([value.get("items"), value.get("data")])
            for candidate in candidates:
                if isinstance(candidate, list):
                    return [item for item in candidate if isinstance(item, dict)]
                if isinstance(candidate, dict) and isinstance(candidate.get("items"), list):
                    return [item for item in candidate["items"] if isinstance(item, dict)]
        return []

    def _filter_items(self, items):
        query = self.search_text.get().strip().lower()
        selected = self.filter_text.get().strip().lower()
        result = []
        for item in items:
            text = " ".join(str(value or "") for value in item.values()).lower()
            if query and query not in text:
                continue
            if selected != "all" and selected not in text:
                continue
            result.append(item)
        return result

    def _fill_metrics(self, monitoring):
        health = monitoring.get("health", {}) if isinstance(monitoring, dict) else {}
        process = health.get("process", health) if isinstance(health, dict) else {}
        agents = monitoring.get("agents", {}) if isinstance(monitoring, dict) else {}
        streams = monitoring.get("streams", {}) if isinstance(monitoring, dict) else {}
        sessions = health.get("sessions", {}) if isinstance(health, dict) else {}
        network = f"{process.get('network_recv_mb', 0)} / {process.get('network_sent_mb', 0)} MB"
        self.metric_labels["CPU"].config(text=f"{process.get('cpu_percent', 0)}%")
        self.metric_labels["RAM"].config(text=f"{process.get('memory_percent', 0)}%")
        self.metric_labels["Disk"].config(text=f"{process.get('disk_percent', 0)}%")
        self.metric_labels["Network"].config(text=network)
        self.metric_labels["Online Agents"].config(text=f"{agents.get('online', 0)} / {agents.get('total', 0)}")
        self.metric_labels["Active Sessions"].config(text=str(sessions.get("active", len(self._last_payload["sessions"]))))

    def _fill_sessions(self, sessions):
        self._clear(self.sessions)
        active = [item for item in sessions if str(item.get("status", "")).lower() in {"active", "pending"}]
        for item in active:
            self.sessions.insert("", tk.END, values=(
                item.get("windows_username") or item.get("user_id") or "",
                item.get("published_app_name") or item.get("app_name") or item.get("server_name") or "Desktop",
                item.get("display_mode") or item.get("connection_type") or "",
                item.get("status") or "",
                self._duration(item.get("duration_seconds")),
            ))

    def _fill_agents(self, agents):
        self._clear(self.agents)
        for item in agents:
            self.agents.insert("", tk.END, values=(
                item.get("agent_id") or "",
                item.get("hostname") or item.get("ip_address") or "",
                item.get("status") or "",
                self._short_time(item.get("last_seen")),
            ))

    def _fill_streams(self, streams):
        self._clear(self.streams)
        for item in streams:
            self.streams.insert("", tk.END, values=(
                item.get("agent_id") or "",
                "Yes" if item.get("active") else "No",
                item.get("viewer_count", item.get("viewers", 0)),
                self._short_time(item.get("last_frame_at")),
            ))

    def _fill_alerts(self, alerts):
        self._clear(self.alerts)
        if not alerts:
            self.alerts.insert("", tk.END, values=("OK", "No active alerts", datetime.now().strftime("%H:%M:%S")))
            return
        for item in alerts:
            self.alerts.insert("", tk.END, values=(
                item.get("level") or item.get("severity") or "Error",
                item.get("message") or item.get("error") or item.get("action") or "",
                self._short_time(item.get("created_at") or item.get("time")),
            ))

    def _fill_events(self, events):
        self._clear(self.events)
        for item in events:
            self.events.insert("", tk.END, values=(
                self._short_time(item.get("created_at") or item.get("timestamp")),
                item.get("action") or item.get("event") or item.get("message") or "",
                item.get("username") or item.get("user_id") or "",
                "OK" if item.get("success", True) else "Failed",
            ))

    def _fill_services(self, monitoring):
        services = monitoring.get("services", {}) if isinstance(monitoring, dict) else {}
        for key, label in self.service_labels.items():
            data = services.get(key, {}) if isinstance(services, dict) else {}
            status = str(data.get("status") or "unknown").lower()
            message = data.get("message") or status.title()
            color = {
                "ok": SUCCESS,
                "healthy": SUCCESS,
                "warning": WARNING,
                "error": DANGER,
            }.get(status, "#edf5f1")
            fg = "white" if color != "#edf5f1" else TEXT
            label.config(
                text=f"{self._service_title(key)}: {status.upper()}",
                bg=color,
                fg=fg,
            )
            label.bind("<Enter>", lambda _event, msg=message: self.app.set_status(msg))

    def _toggle_auto_refresh(self):
        if self.auto_refresh.get():
            self.refresh()
        elif self._auto_job:
            self.after_cancel(self._auto_job)
            self._auto_job = None

    def _schedule_auto_refresh(self):
        if self._auto_job:
            self.after_cancel(self._auto_job)
            self._auto_job = None
        if self.auto_refresh.get():
            self._auto_job = self.after(AUTO_REFRESH_MS, self.refresh)

    def _clear(self, tree):
        children = tree.get_children()
        if children:
            tree.delete(*children)

    def _duration(self, seconds):
        try:
            seconds = int(seconds or 0)
        except (TypeError, ValueError):
            seconds = 0
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"

    def _short_time(self, value):
        if not value:
            return ""
        text = str(value)
        if "T" in text:
            text = text.replace("T", " ")
        return text[:19]

    def _service_title(self, key):
        return {
            "backend": "Backend",
            "database": "Database",
            "guacamole": "Guacamole",
            "api": "API",
            "license": "License Server",
        }.get(key, key.title())

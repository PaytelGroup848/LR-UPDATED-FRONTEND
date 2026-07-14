"""
Floating product-key panel for the LR desktop agent.

Behaviour (as decided with the client):
  - First run on a device gets a 7 day free trial automatically.
  - While the trial is active, a small floating "N days left" pill is
    shown in a corner of the screen - non-blocking, app keeps working.
  - The moment the trial (or a paid license) runs out, the agent calls
    hold() with whatever "current work context" it was given, then this
    panel switches into a blocking key-entry mode: a small always-on-top
    window asking for the product key, app stays paused behind it.
  - Once a valid key is entered, the backend returns the resume_context
    that was stored at hold() time, and the agent uses it to continue
    exactly from where it left off instead of restarting the session.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from agent.license.license_client import LicenseClient
from agent.license.device_id import get_device_id


STATUS_POLL_MS = 60_000


class ProductKeyPanel(QWidget):

    def __init__(
        self,
        base_url: str,
        get_current_context=None,
        on_activated=None,
        device_name: str | None = None
    ):
        super().__init__()

        self.client = LicenseClient(base_url)
        self.device_id = get_device_id()
        self.device_name = device_name
        self.get_current_context = get_current_context or (lambda: None)
        self.on_activated = on_activated or (lambda ctx: None)

        self._build_ui()

        self.client.start_trial(self.device_id, self.device_name)

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.refresh_status)
        self.poll_timer.start(STATUS_POLL_MS)

        self.refresh_status()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedWidth(300)
        self.setStyleSheet(
            "QWidget { background-color: #1f2330; border-radius: 10px; }"
            "QLabel { color: #f1f2f6; }"
            "QLineEdit { background-color: #2b2f3f; color: #ffffff; "
            "border: 1px solid #3a3f52; border-radius: 6px; padding: 6px; }"
            "QPushButton { background-color: #4f6df5; color: white; "
            "border-radius: 6px; padding: 6px 10px; }"
            "QPushButton:hover { background-color: #3d5ae0; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        self.title_label = QLabel("LR Platform")
        self.title_label.setStyleSheet("font-weight: 600; font-size: 13px;")

        self.status_label = QLabel("Checking license...")
        self.status_label.setStyleSheet("font-size: 12px; color: #b7bccb;")
        self.status_label.setWordWrap(True)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("LR-XXXXX-XXXXX-XXXXX-XXXXX")
        self.key_input.returnPressed.connect(self.try_activate)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("font-size: 11px; color: #ff6b6b;")
        self.error_label.setWordWrap(True)

        button_row = QHBoxLayout()
        self.activate_button = QPushButton("Activate")
        self.activate_button.clicked.connect(self.try_activate)
        button_row.addStretch()
        button_row.addWidget(self.activate_button)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.key_input)
        layout.addLayout(button_row)
        layout.addWidget(self.error_label)

        self._position_bottom_right()

    def _position_bottom_right(self):

        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        margin = 24
        x = screen.right() - self.width() - margin
        y = screen.bottom() - self.height() - margin
        self.move(x, y)

    # ------------------------------------------------------------------
    # Status / blocking logic
    # ------------------------------------------------------------------

    def refresh_status(self):

        try:
            status = self.client.get_status(self.device_id)

        except Exception:
            self.status_label.setText(
                "Could not reach license server. Retrying..."
            )
            return

        state = status.get("status")

        if state == "LICENSED":
            self._unblock()
            return

        if state == "TRIAL_ACTIVE":
            days = status.get("days_remaining", 0)
            self._show_trial_countdown(days)
            return

        if state in ("TRIAL_EXPIRED", "HELD", "NOT_FOUND"):
            self._enter_blocking_mode(already_held=(state == "HELD"))
            return

    def _show_trial_countdown(self, days_remaining: int):

        self.key_input.hide()
        self.activate_button.hide()
        self.error_label.hide()

        self.status_label.setText(
            f"Free trial - {days_remaining} day(s) left. "
            "App is fully usable."
        )

        self._position_bottom_right()
        self.show()

    def _enter_blocking_mode(self, already_held: bool):

        if not already_held:
            context = self.get_current_context()
            try:
                self.client.hold(self.device_id, context)
            except Exception:
                pass

        self.status_label.setText(
            "Your free trial has ended. Enter a product key to "
            "continue - your work will resume right where it paused."
        )
        self.key_input.show()
        self.activate_button.show()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self._position_bottom_right()
        self.show()
        self.raise_()
        self.activateWindow()
        self.key_input.setFocus()

    def _unblock(self):

        self.poll_timer.stop()
        self.hide()

    def try_activate(self):

        key_code = self.key_input.text().strip()

        if not key_code:
            self.error_label.setText("Please enter a product key.")
            self.error_label.show()
            return

        try:
            result = self.client.activate(
                key_code=key_code,
                device_id=self.device_id,
                device_name=self.device_name
            )

        except ValueError as error:
            self.error_label.setText(str(error))
            self.error_label.show()
            return

        except Exception:
            self.error_label.setText(
                "Could not reach license server. Try again."
            )
            self.error_label.show()
            return

        self.error_label.hide()
        self.on_activated(result.get("resume_context"))
        self._unblock()

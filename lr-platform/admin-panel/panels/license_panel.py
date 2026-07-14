from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QFormLayout
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QTableWidget
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QMessageBox


class LicensePanel(QWidget):
    # "Product Keys" tab inside the LR Admin Panel.

    def __init__(self, client):
        super().__init__()

        self.client = client

        layout = QVBoxLayout(self)

        layout.addWidget(self._build_generate_box())

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Key", "Plan", "Activations", "Valid Days", "Status"]
        )
        header = self.table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        layout.addWidget(self.table)

        actions_row = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_keys)
        revoke_button = QPushButton("Revoke Selected")
        revoke_button.clicked.connect(self.revoke_selected)
        actions_row.addWidget(refresh_button)
        actions_row.addWidget(revoke_button)
        actions_row.addStretch()
        layout.addLayout(actions_row)

        self.load_keys()

    def _build_generate_box(self) -> QGroupBox:

        box = QGroupBox("Generate Product Key(s)")
        form = QFormLayout(box)

        self.plan_input = QLineEdit("STANDARD")
        self.valid_days_input = QSpinBox()
        self.valid_days_input.setRange(1, 3650)
        self.valid_days_input.setValue(365)

        self.issued_to_input = QLineEdit()
        self.issued_to_input.setPlaceholderText("Customer name (optional)")

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 500)
        self.quantity_input.setValue(1)

        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(self.generate_keys)

        form.addRow("Plan name", self.plan_input)
        form.addRow("VM limit", QLabel("1 VM per key, transfer after 90 days"))
        form.addRow("Valid for (days)", self.valid_days_input)
        form.addRow("Issued to", self.issued_to_input)
        form.addRow("Quantity", self.quantity_input)
        form.addRow(generate_button)

        return box

    def generate_keys(self):

        try:
            keys = self.client.create_product_keys(
                plan_name=self.plan_input.text().strip() or "STANDARD",
                max_activations=1,
                valid_days=self.valid_days_input.value(),
                issued_to=self.issued_to_input.text().strip() or None,
                quantity=self.quantity_input.value()
            )

        except Exception as error:
            QMessageBox.warning(self, "Could not generate key", str(error))
            return

        codes = "\n".join(key["key_code"] for key in keys)
        QMessageBox.information(
            self, "Product key(s) generated", codes
        )
        self.load_keys()

    def load_keys(self):

        try:
            keys = self.client.list_product_keys()
        except Exception as error:
            QMessageBox.warning(self, "Could not load keys", str(error))
            return

        self.table.setRowCount(len(keys))

        for row, key in enumerate(keys):
            self.table.setItem(row, 0, QTableWidgetItem(key["key_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(key["plan_name"]))
            self.table.setItem(
                row, 2, QTableWidgetItem(str(key["max_activations"]))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(str(key["valid_days"]))
            )
            status = "REVOKED" if key["is_revoked"] else "ACTIVE"
            self.table.setItem(row, 4, QTableWidgetItem(status))

    def revoke_selected(self):

        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(self, "No selection", "Select a key first.")
            return

        key_item = self.table.item(row, 0)
        if key_item is None:
            QMessageBox.information(self, "No selection", "Select a key first.")
            return

        key_code = key_item.text()

        confirm = QMessageBox.question(
            self,
            "Revoke key",
            f"Revoke product key {key_code}? This cannot be undone."
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.client.revoke_product_key(key_code)
        except Exception as error:
            QMessageBox.warning(self, "Could not revoke key", str(error))
            return

        self.load_keys()

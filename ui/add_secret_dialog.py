from PySide6.QtWidgets import (
    QDialog, QLineEdit, QVBoxLayout, QFormLayout, 
    QDialogButtonBox, QPushButton
)
from .theme import COLORS

class AddSecretDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Secret")
        self.setMinimumWidth(350)

        self.key_input = QLineEdit()
        self.value_input = QLineEdit()
        self.value_input.setEchoMode(QLineEdit.Password)

        form_layout = QFormLayout()
        form_layout.addRow("Key:", self.key_input)
        form_layout.addRow("Value:", self.value_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS["BACKGROUND_PRIMARY"].name()}; }}
            QLineEdit {{ border: 1px solid {COLORS["BORDER_DEFAULT"].name()}; padding: 8px; border-radius: 4px; }}
        """)

    def get_values(self):
        return self.key_input.text(), self.value_input.text()

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel, 
    QGroupBox, QHBoxLayout, QTableWidget, QHeaderView, QPushButton, QTableWidgetItem, QMessageBox, QFileDialog
)
from PySide6.QtCore import Signal, Qt, Slot
from core.config_manager import ConfigManager
from .animated_button import AnimatedButton
from .add_secret_dialog import AddSecretDialog
from .theme import COLORS, get_font

class SettingsPanel(QWidget):
    """设置面板，用于显示和修改 wrangler.toml 的配置。"""
    login_requested = Signal()
    logout_requested = Signal()

    def __init__(self, command_manager, parent=None):
        super().__init__(parent)
        self.command_manager = command_manager
        self.config_manager = None
        self._setup_ui()
        self._setup_styles()
        self.command_manager.json_received.connect(self._on_secrets_loaded)
        self.command_manager.process_finished.connect(self._on_secret_process_finished)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(32, 32, 32, 32)
        self.main_layout.setSpacing(24)
        self.main_layout.setAlignment(Qt.AlignTop)

        # --- 账户认证组 ---
        account_group = self._create_account_group()
        
        # --- 项目配置组 ---
        project_group = self._create_project_group()

        # --- Secrets 管理组 ---
        secrets_group = self._create_secrets_group()

        self.main_layout.addWidget(account_group)
        self.main_layout.addWidget(project_group)
        self.main_layout.addWidget(secrets_group)
        self.main_layout.addStretch()

    def _create_account_group(self):
        group = QGroupBox("ACCOUNT AUTHENTICATION")
        layout = QVBoxLayout()
        layout.setSpacing(12)

        login_button = AnimatedButton("Login to Cloudflare", button_type='primary')
        login_button.clicked.connect(self.login_requested)
        logout_button = AnimatedButton("Logout", button_type='outline')
        logout_button.clicked.connect(self.logout_requested)

        layout.addWidget(login_button)
        layout.addWidget(logout_button)
        group.setLayout(layout)
        return group

    def _create_project_group(self):
        group = QGroupBox("PROJECT CONFIGURATION (WRANGLER.TOML)")
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(12)
        self.form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.name_input = QLineEdit()
        self.main_input = QLineEdit()
        self.compatibility_date_input = QLineEdit()

        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("Main Entrypoint:", self.main_input)
        self.form_layout.addRow("Compatibility Date:", self.compatibility_date_input)

        save_button_layout = QHBoxLayout()
        self.save_button = AnimatedButton("Save Settings", button_type='primary')
        self.save_button.clicked.connect(self.save_settings)
        save_button_layout.addStretch()
        save_button_layout.addWidget(self.save_button)
        save_button_layout.addStretch()

        form_widget = QWidget()
        form_widget.setLayout(self.form_layout)

        container_layout = QVBoxLayout()
        container_layout.addWidget(form_widget)
        container_layout.addSpacing(20)
        container_layout.addLayout(save_button_layout)

        group.setLayout(container_layout)
        return group

    def _create_secrets_group(self):
        group = QGroupBox("SECRETS")
        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.secrets_table = QTableWidget()
        self.secrets_table.setColumnCount(3)
        self.secrets_table.setHorizontalHeaderLabels(["Key", "Value", "Actions"])
        self.secrets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.secrets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.secrets_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.secrets_table.verticalHeader().setVisible(False)
        self.secrets_table.setEditTriggers(QTableWidget.NoEditTriggers)

        button_layout = QHBoxLayout()
        add_secret_button = AnimatedButton("Add Secret", button_type='primary')
        add_secret_button.clicked.connect(self._on_add_secret)
        bulk_import_button = AnimatedButton("Bulk Import .env", button_type='outline')
        bulk_import_button.clicked.connect(self._on_bulk_import)
        button_layout.addWidget(add_secret_button)
        button_layout.addWidget(bulk_import_button)
        button_layout.addStretch()

        layout.addWidget(self.secrets_table)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def load_secrets(self):
        if self.config_manager and self.config_manager.project_path:
            self.secrets_table.setRowCount(0) # Clear table
            self.command_manager.execute("wrangler", ["secret", "list"], self.config_manager.project_path)

    @Slot(object)
    def _on_secrets_loaded(self, secrets):
        # This assumes the JSON output is a list of objects with a 'name' key.
        if not isinstance(secrets, list) or not all('name' in s for s in secrets):
            return # Not the data we are looking for

        self.secrets_table.setRowCount(len(secrets))
        for i, secret in enumerate(secrets):
            key_item = QTableWidgetItem(secret['name'])
            value_item = QTableWidgetItem("••••••••")
            
            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("color: #F6821F; border: none;")
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.clicked.connect(lambda checked, key=secret['name']: self._on_delete_secret(key))

            self.secrets_table.setItem(i, 0, key_item)
            self.secrets_table.setItem(i, 1, value_item)
            self.secrets_table.setCellWidget(i, 2, delete_button)

    @Slot(str)
    def _on_delete_secret(self, key):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete the secret '{key}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.command_manager.execute("wrangler", ["secret", "delete", key], self.config_manager.project_path)

    @Slot()
    def _on_add_secret(self):
        dialog = AddSecretDialog(self)
        if dialog.exec():
            key, value = dialog.get_values()
            if key and value:
                self.command_manager.execute("wrangler", ["secret", "put", key], self.config_manager.project_path, stdin=value.encode())

    @Slot()
    def _on_bulk_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .env file", "", "Env files (*.env)")
        if file_path:
            self.command_manager.execute("wrangler", ["secret", "bulk", file_path], self.config_manager.project_path)

    @Slot(int, object)
    def _on_secret_process_finished(self, exit_code, exit_status):
        # Check if the process finished successfully
        if exit_status == 0 and exit_code == 0:
            # A bit of a delay to allow wrangler to process the change
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self.load_secrets)

    def _create_shortcut_guide(self):
        group = QGroupBox("KEYBOARD SHORTCUTS")
        layout = QFormLayout()
        layout.setSpacing(8)

        shortcuts = {
            "Save Current File": "Cmd+S",
            "Save All Files": "Cmd+Shift+S",
            "Open Project": "Cmd+O",
            "New File": "Cmd+N",
            "Close Current Tab": "Cmd+W",
            "Toggle Dev Mode": "Cmd+R",
            "Deploy Project": "Cmd+Shift+D",
            "Toggle Output Panel": "Ctrl+`",
            "Toggle Sidebar": "Cmd+B",
            "Open Settings": "Cmd+,",
        }

        for action, shortcut in shortcuts.items():
            layout.addRow(QLabel(action), QLabel(shortcut))

        group.setLayout(layout)
        return group

    def _setup_styles(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                font-family: {get_font("SECTION_TITLE").family()};
                font-size: 12px;
                color: {COLORS["TEXT_MUTED"].name()};
                border: none;
                margin-top: 16px;
            }}
            QGroupBox::title {{ 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                padding: 0; 
                left: 0;
            }}
            QLineEdit {{
                background-color: {COLORS["BACKGROUND_PRIMARY"].name()};
                color: {COLORS["TEXT_PRIMARY"].name()};
                border: 1px solid {COLORS["BORDER_DEFAULT"].name()};
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 36px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS["ACCENT_ORANGE"].name()};
                outline: none;
            }}
            QFormLayout QLabel {{
                color: {COLORS["TEXT_SECONDARY"].name()};
                padding-bottom: 4px;
            }}
        """)

    def set_project(self, project_path):
        self.config_manager = ConfigManager(project_path)
        self.load_settings()

    def load_settings(self):
        if self.config_manager and self.config_manager.data:
            self.name_input.setText(self.config_manager.get('name', ''))
            self.main_input.setText(self.config_manager.get('main', ''))
            self.compatibility_date_input.setText(self.config_manager.get('compatibility_date', ''))
            self.save_button.setEnabled(True)
        else:
            self.name_input.clear()
            self.main_input.clear()
            self.compatibility_date_input.clear()
            self.save_button.setEnabled(False)

    def save_settings(self):
        if self.config_manager:
            self.config_manager.set('name', self.name_input.text())
            self.config_manager.set('main', self.main_input.text())
            self.config_manager.set('compatibility_date', self.compatibility_date_input.text())
            self.config_manager.save()

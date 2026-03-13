
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox
from PySide6.QtCore import Signal
from core.config_manager import ConfigManager
from .animated_button import AnimatedButton

class SettingsPanel(QWidget):
    """设置面板，用于显示和修改 wrangler.toml 的配置。"""
    login_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = None
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        # --- 账户认证组 ---
        account_group = QGroupBox("Cloudflare Account")
        account_layout = QVBoxLayout()

        login_button = AnimatedButton("Login")
        login_button.clicked.connect(self.login_requested)
        logout_button = AnimatedButton("Logout")
        logout_button.clicked.connect(self.logout_requested)

        account_layout.addWidget(login_button)
        account_layout.addWidget(logout_button)
        account_group.setLayout(account_layout)

        # --- 项目配置组 ---
        project_group = QGroupBox("Project Configuration")
        self.form_layout = QFormLayout()
        project_group.setLayout(self.form_layout)

        # 为常见的配置项创建输入框
        self.name_input = QLineEdit()
        self.main_input = QLineEdit()
        self.compatibility_date_input = QLineEdit()

        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("Main Entrypoint:", self.main_input)
        self.form_layout.addRow("Compatibility Date:", self.compatibility_date_input)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)

        self.main_layout.addWidget(account_group)
        self.main_layout.addWidget(project_group)
        self.main_layout.addWidget(self.save_button)
        self.main_layout.addStretch()

    def set_project(self, project_path):
        """加载一个新项目并更新UI。"""
        self.config_manager = ConfigManager(project_path)
        self.load_settings()

    def load_settings(self):
        """从 ConfigManager 加载数据并填充到输入框。"""
        if self.config_manager and self.config_manager.data:
            self.name_input.setText(self.config_manager.get('name', ''))
            self.main_input.setText(self.config_manager.get('main', ''))
            self.compatibility_date_input.setText(self.config_manager.get('compatibility_date', ''))
            self.save_button.setEnabled(True)
        else:
            # 如果没有配置文件，则清空并禁用
            self.name_input.clear()
            self.main_input.clear()
            self.compatibility_date_input.clear()
            self.save_button.setEnabled(False)

    def save_settings(self):
        """将UI中的数据保存回 wrangler.toml。"""
        if self.config_manager:
            self.config_manager.set('name', self.name_input.text())
            self.config_manager.set('main', self.main_input.text())
            self.config_manager.set('compatibility_date', self.compatibility_date_input.text())
            self.config_manager.save()
            # 可以在这里加一个状态提示，比如在日志面板显示 "Settings saved!"

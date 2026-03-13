
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from .animated_button import AnimatedButton

class WelcomeScreen(QWidget):
    """一个居中卡片式的欢迎界面，用于引导用户打开项目。"""
    open_project_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # --- Main Layout (to center the card) ---
        main_layout = QHBoxLayout(self)
        main_layout.addStretch()

        # --- Card Layout ---
        card_frame = QFrame(self)
        card_frame.setObjectName("welcomeCard")
        card_frame.setFixedSize(400, 220)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(16)

        # --- Content ---
        title = QLabel("Wrangler GUI")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("A modern interface for Cloudflare Workers")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        open_button = AnimatedButton("Open a Project")
        open_button.clicked.connect(self.open_project_requested)

        # --- Assembly ---
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addStretch()
        card_layout.addWidget(open_button)
        
        main_layout.addWidget(card_frame)
        main_layout.addStretch()

        # --- Specific Styling for the Card ---
        self.setStyleSheet("""
            #welcomeCard {
                background-color: rgba(30, 30, 30, 0.8);
                border: 1px solid #292929;
                border-radius: 6px;
            }
            #welcomeTitle {
                font-size: 24px;
                font-weight: bold;
            }
            #welcomeSubtitle {
                color: #888888;
            }
        """)

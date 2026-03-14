import subprocess
from PySide6.QtCore import (
    Qt, Signal, QSize, QPoint, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, Property, QRect, QPointF
)
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QApplication, QGraphicsOpacityEffect
)
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QFont, QScreen

from . import theme

class WelcomeScreen(QWidget):
    open_project_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self._scale = 1.0
        theme.initialize_fonts()
        self._setup_window()
        self._setup_ui()
        self._setup_animations()

    def _setup_window(self):
        self.setFixedSize(520, 360)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignCenter)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setContentsMargins(0,0,0,0)
        content_widget.setFixedWidth(320)
        content_widget.move(0, -20)

        icon_label = QLabel("⚡")
        icon_font = QFont(theme.SYSTEM_FONT, 32)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(64, 64)
        icon_label.setStyleSheet("background-color: rgba(255,255,255,0.22); border-radius: 12px; color: white;")
        content_layout.addWidget(icon_label, 0, Qt.AlignCenter)
        content_layout.addSpacing(20)

        title_label = QLabel("Wrangler GUI")
        title_font = QFont(theme.FONTS["UI_BOLD"])
        title_font.setPointSize(28)
        title_font.setLetterSpacing(QFont.PercentageSpacing, 99.5)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FFFFFF;")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        content_layout.addSpacing(8)

        subtitle_label = QLabel("A modern interface for Cloudflare Workers")
        subtitle_font = QFont(theme.FONTS["UI"])
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: rgba(255,255,255,0.80);")
        subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle_label)
        content_layout.addSpacing(36)

        self.open_button = QPushButton("Open a Project")
        self.open_button.setFixedSize(280, 48)
        button_font = QFont(theme.FONTS["UI_BOLD"])
        button_font.setPointSize(15)
        self.open_button.setFont(button_font)
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #F6821F; border-radius: 10px; border: none; }
            QPushButton:hover { background-color: rgba(255,255,255,0.90); }
        """)
        self.open_button.clicked.connect(self.open_project_requested.emit)
        
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.open_button)
        button_container.addStretch()
        content_layout.addLayout(button_container)
        content_layout.addSpacing(20)

        version_label = QLabel(self._get_wrangler_version())
        version_font = QFont(theme.FONTS["UI"])
        version_font.setPointSize(11)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: rgba(255,255,255,0.45);")
        version_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(version_label)

        self.main_layout.addWidget(content_widget)

    def _get_wrangler_version(self):
        try:
            result = subprocess.run(["wrangler", "--version"], capture_output=True, text=True, timeout=3, check=True)
            return result.stdout.splitlines()[0].strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def _setup_animations(self):
        self.press_anim = QPropertyAnimation(self, b"scale")
        self.press_anim.setDuration(80)
        self.press_anim.setEndValue(0.95)
        
        self.release_anim = QPropertyAnimation(self, b"scale")
        self.release_anim.setDuration(150)
        self.release_anim.setEndValue(1.0)
        self.release_anim.setEasingCurve(QEasingCurve.OutBack)

        self.open_button.pressed.connect(self.press_anim.start)
        self.open_button.released.connect(self.release_anim.start)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim_opacity = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_opacity.setDuration(250)
        self.anim_opacity.setStartValue(0.0)
        self.anim_opacity.setEndValue(1.0)
        self.anim_opacity.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_geometry = QPropertyAnimation(self, b"geometry")
        self.anim_geometry.setDuration(250)
        self.anim_geometry.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.anim_opacity)
        self.anim_group.addAnimation(self.anim_geometry)

    def showEvent(self, event):
        screen_geometry = QScreen.availableGeometry(self.screen())
        center_pos = screen_geometry.center()
        start_pos = QPoint(center_pos.x() - self.width() / 2, center_pos.y() - self.height() / 2 + 12)
        end_pos = QPoint(center_pos.x() - self.width() / 2, center_pos.y() - self.height() / 2)
        
        self.setGeometry(start_pos.x(), start_pos.y(), self.width(), self.height())
        self.anim_geometry.setStartValue(self.geometry())
        self.anim_geometry.setEndValue(QRect(end_pos, self.size()))
        
        self.anim_group.start()
        super().showEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        transform = painter.transform()
        transform.translate(self.width() / 2, self.height() / 2)
        transform.scale(self._scale, self._scale)
        transform.translate(-self.width() / 2, -self.height() / 2)
        painter.setTransform(transform)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#F6821F"))
        gradient.setColorAt(1.0, QColor("#FBAD41"))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)

    def get_scale(self):
        return self._scale

    def set_scale(self, scale):
        self._scale = scale
        self.update()

    scale = Property(float, get_scale, set_scale)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

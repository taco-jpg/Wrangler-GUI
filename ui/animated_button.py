from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from .theme import COLORS, get_font
from .animations import apply_spring_click_animation

class AnimatedButton(QPushButton):
    """一个支持颜色动画和缩放动画的按钮，样式由theme.py定义。"""

    def __init__(self, text="", parent=None, button_type='primary'):
        super().__init__(text, parent)
        self.button_type = button_type
        self._setup_style()

        self.color_animation = QPropertyAnimation(self, b"color")
        self.color_animation.setDuration(150)
        self.color_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # 应用Spring动画
        apply_spring_click_animation(self)

    def _setup_style(self):
        self.setFont(get_font("UI_BOLD"))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("padding: 8px 20px; border-radius: 6px;")

        if self.button_type == 'primary':
            self.default_color = COLORS["ACCENT_ORANGE"]
            self.hover_color = COLORS["ACCENT_ORANGE_HOVER"]
            self.pressed_color = COLORS["ACCENT_ORANGE_PRESS"]
            self.text_color = QColor("#FFFFFF")
            self.border_color = Qt.transparent
        elif self.button_type == 'secondary':
            self.default_color = QColor("#FFFFFF")
            self.hover_color = COLORS["BACKGROUND_SECONDARY"]
            self.pressed_color = COLORS["BACKGROUND_TERTIARY"]
            self.text_color = COLORS["TEXT_PRIMARY"]
            self.border_color = COLORS["BORDER_STRONG"]
        elif self.button_type == 'outline':
            self.default_color = QColor("#FFFFFF")
            self.hover_color = COLORS["ACCENT_ORANGE_LIGHT"]
            self.pressed_color = COLORS["ACCENT_ORANGE_LIGHT"]
            self.text_color = COLORS["ACCENT_ORANGE"]
            self.border_color = COLORS["ACCENT_ORANGE"]
        
        self._color = self.default_color

    def enterEvent(self, event):
        self.color_animation.setEndValue(self.hover_color)
        self.color_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.color_animation.setEndValue(self.default_color)
        self.color_animation.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.color_animation.setEndValue(self.pressed_color)
        self.color_animation.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.color_animation.setEndValue(self.hover_color)
        self.color_animation.start()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(self._color)
        painter.setPen(self.border_color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 5, 5)

        painter.setPen(self.text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def _get_color(self):
        return self._color

    def _set_color(self, color):
        self._color = color
        self.update()

    color = Property(QColor, _get_color, _set_color)

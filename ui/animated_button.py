
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor, QPainter, QPaintEvent

class AnimatedButton(QPushButton):
    """一个背景颜色可以平滑过渡的按钮。"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # 使用支持 alpha 通道的 QColor
        self._color = QColor("rgba(255, 255, 255, 0.05)")
        self.hover_color = QColor("rgba(255, 255, 255, 0.1)")
        self.pressed_color = QColor("rgba(255, 255, 255, 0.12)")
        self.default_color = self._color

        self.animation = QPropertyAnimation(self, b"color")
        self.animation.setDuration(100) # 严格设置为 100ms
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

    def enterEvent(self, event):
        """鼠标进入事件，触发悬停动画。"""
        self.animation.setEndValue(self.hover_color)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件，恢复默认颜色。"""
        self.animation.setEndValue(self.default_color)
        self.animation.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下事件，变为按下颜色。"""
        self.animation.setEndValue(self.pressed_color)
        self.animation.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件，恢复悬停颜色。"""
        self.animation.setEndValue(self.hover_color)
        self.animation.start()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent):
        """重写绘图事件，手动绘制背景。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6) # 6px 圆角

        # 绘制文本
        painter.setPen(QColor("#f0f0f0"))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def _get_color(self):
        return self._color

    def _set_color(self, color):
        self._color = color
        self.update() # 颜色改变时，请求重绘

    color = Property(QColor, _get_color, _set_color)

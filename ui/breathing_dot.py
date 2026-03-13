from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPaintEvent
from PySide6.QtWidgets import QWidget
from .theme import COLORS

class BreathingDot(QWidget):
    """一个可以根据状态改变颜色和动画的脉冲圆点。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._radius = 4
        self._color = Qt.transparent
        self.setFixedSize(QSize(16, 16))

        self.animation = QPropertyAnimation(self, b"radius")
        self.animation.setDuration(1000)
        self.animation.setStartValue(3)
        self.animation.setEndValue(6)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.setLoopCount(-1)

    def set_state(self, state: str):
        """设置点的状态：'running', 'success', 'error', or 'idle'"""
        if state == 'running':
            self._color = COLORS["ACCENT_ORANGE"]
            self.animation.start()
            self.show()
        elif state == 'success':
            self._color = COLORS["SUCCESS"]
            self.animation.stop()
            self._radius = 5
            self.update()
            self.show()
        elif state == 'error':
            self._color = COLORS["ERROR"]
            self.animation.stop()
            self._radius = 5
            self.update()
            self.show()
        else: # idle
            self._color = Qt.transparent
            self.animation.stop()
            self.hide()
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        center = self.rect().center()
        painter.drawEllipse(center, self._radius, self._radius)

    def _get_radius(self):
        return self._radius

    def _set_radius(self, radius):
        self._radius = radius
        self.update()

    radius = Property(float, _get_radius, _set_radius)

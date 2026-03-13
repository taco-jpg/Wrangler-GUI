
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QPaintEvent

class BreathingDot(QWidget):
    """一个会产生呼吸效果的小圆点，用于状态栏加载动画。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._radius = 0
        self._color = QColor("#007acc") # Cloudflare Blue

        self.setFixedSize(20, 20)

        # 半径动画 (从小到大)
        self.radius_anim_in = QPropertyAnimation(self, b"radius")
        self.radius_anim_in.setDuration(1000)
        self.radius_anim_in.setStartValue(0)
        self.radius_anim_in.setEndValue(8)
        self.radius_anim_in.setEasingCurve(QEasingCurve.InOutSine)

        # 半径动画 (从大到小)
        self.radius_anim_out = QPropertyAnimation(self, b"radius")
        self.radius_anim_out.setDuration(1000)
        self.radius_anim_out.setStartValue(8)
        self.radius_anim_out.setEndValue(0)
        self.radius_anim_out.setEasingCurve(QEasingCurve.InOutSine)

        # 创建一个循环的动画组
        self.anim_group = QSequentialAnimationGroup(self)
        self.anim_group.addAnimation(self.radius_anim_in)
        self.anim_group.addAnimation(self.radius_anim_out)
        self.anim_group.setLoopCount(-1) # 无限循环

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

    def start(self):
        self.anim_group.start()
        self.show()

    def stop(self):
        self.anim_group.stop()
        self.hide()

    radius = Property(float, _get_radius, _set_radius)

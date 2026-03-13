from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QObject, Property, QPointF
from PySide6.QtWidgets import QGraphicsEffect, QWidget
from PySide6.QtGui import QPainter

class ScaleEffect(QGraphicsEffect):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0

    def setScale(self, scale):
        self._scale = scale
        self.update()

    def scale(self):
        return self._scale

    def draw(self, painter: QPainter):
        source = self.sourcePixmap()
        if not source.isNull():
            transform = painter.transform()
            transform.translate(source.width() / 2, source.height() / 2)
            transform.scale(self._scale, self._scale)
            transform.translate(-source.width() / 2, -source.height() / 2)
            painter.setWorldTransform(transform)
            painter.drawPixmap(QPointF(0, 0), source)

    scale_property = Property(float, fget=scale, fset=setScale)

def apply_spring_click_animation(widget: QWidget):
    """为给定的QWidget应用一个弹簧点击动画。"""
    scale_effect = ScaleEffect(widget)
    widget.setGraphicsEffect(scale_effect)

    press_anim = QPropertyAnimation(scale_effect, b"scale_property")
    press_anim.setDuration(80)
    press_anim.setEasingCurve(QEasingCurve.OutQuad)
    press_anim.setEndValue(0.94)

    release_anim_group = QSequentialAnimationGroup()
    anim_up = QPropertyAnimation(scale_effect, b"scale_property")
    anim_up.setDuration(150)
    easing_up = QEasingCurve(QEasingCurve.Type.OutBack)
    easing_up.setAmplitude(3.0)
    anim_up.setEasingCurve(easing_up)
    anim_up.setEndValue(1.04)

    anim_down = QPropertyAnimation(scale_effect, b"scale_property")
    anim_down.setDuration(100)
    anim_down.setEasingCurve(QEasingCurve.OutQuad)
    anim_down.setEndValue(1.0)

    release_anim_group.addAnimation(anim_up)
    release_anim_group.addAnimation(anim_down)

    original_press_event = widget.mousePressEvent
    original_release_event = widget.mouseReleaseEvent

    def new_press_event(event):
        press_anim.start()
        original_press_event(event)

    def new_release_event(event):
        release_anim_group.start()
        original_release_event(event)

    widget.mousePressEvent = new_press_event
    widget.mouseReleaseEvent = new_release_event

def apply_pulse_animation(widget: QWidget):
    """为给定的QWidget应用一个脉冲（透明度）动画。"""
    pulse_anim = QPropertyAnimation(widget, b"windowOpacity")
    pulse_anim.setDuration(1000)
    pulse_anim.setLoopCount(-1)
    pulse_anim.setKeyValueAt(0, 1.0)
    pulse_anim.setKeyValueAt(0.5, 0.5)
    pulse_anim.setKeyValueAt(1, 1.0)
    return pulse_anim

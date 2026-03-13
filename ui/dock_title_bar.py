
import os
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QStyle, QApplication
from PySide6.QtGui import QIcon

class DockTitleBar(QWidget):
    """一个自定义的 Dock Widget 标题栏，包含自定义的控制按钮。"""
    kill_process_requested = Signal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        layout.addWidget(self.title_label)
        layout.addStretch()

        style = QApplication.style()

        # 中止进程按钮 (垃圾桶)
        self.kill_button = QToolButton()
        self.kill_button.setIcon(style.standardIcon(QStyle.SP_TrashIcon))
        self.kill_button.setIconSize(QSize(14, 14))
        self.kill_button.setAutoRaise(True)
        self.kill_button.clicked.connect(self.kill_process_requested)

        # 隐藏按钮 (X)
        self.hide_button = QToolButton()
        self.hide_button.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))
        self.hide_button.setIconSize(QSize(14, 14))
        self.hide_button.setAutoRaise(True)
        # 隐藏按钮的点击事件将连接到 dock widget 的 hide 方法

        layout.addWidget(self.kill_button)
        layout.addWidget(self.hide_button)

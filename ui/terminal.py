from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import QProcess
from PySide6.QtGui import QColor
from .theme import COLORS, get_font

class Terminal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.terminal_output = QPlainTextEdit(self)
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(get_font("CODE"))
        self.terminal_output.setStyleSheet(f"background-color: {COLORS['CODE_BG'].name()}; color: #E0E0E0; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.terminal_output)

        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.start("/bin/zsh")

    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.terminal_output.appendPlainText(data)

    def handle_error(self):
        data = self.process.readAllStandardError().data().decode()
        self.terminal_output.appendPlainText(data)

    def keyPressEvent(self, event):
        self.process.write(event.text().encode())
        super().keyPressEvent(event)

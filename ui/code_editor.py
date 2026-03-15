import re
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QColor, QPainter, QTextFormat, QSyntaxHighlighter, QTextCharFormat, QFont, QKeySequence

from .theme import COLORS, get_font

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)

class JSHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#C678DD"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["\\bfunction\\b", "\\bconst\\b", "\\blet\\b", "\\bvar\\b", 
                    "\\breturn\\b", "\\bif\\b", "\\belse\\b", "\\bfor\\b", 
                    "\\bwhile\\b", "\\bswitch\\b", "\\bcase\\b", "\\bbreak\\b",
                    "\\bawait\\b", "\\basync\\b", "\\bnew\\b", "\\bimport\\b", "\\bfrom\\b"]
        self.highlighting_rules += [(re.compile(pattern), keyword_format) for pattern in keywords]

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98C379"))
        self.highlighting_rules.append((re.compile('".*?"'), string_format))
        self.highlighting_rules.append((re.compile("'.*?'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5C6370"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile("//[^\n]*"), comment_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#D19A66"))
        self.highlighting_rules.append((re.compile("\\b[0-9]+\\b"), number_format))

        function_call_format = QTextCharFormat()
        function_call_format.setForeground(QColor("#61AFEF"))
        self.highlighting_rules.append((re.compile("\\b([A-Za-z0-9_]+)(?=\\()"), function_call_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.highlighter = JSHighlighter(self.document())

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self._setup_style()

    def _setup_style(self):
        self.setFont(get_font("CODE"))
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLORS["CODE_BG"].name()};
                color: #E0E0E0;
                border: none;
                padding-left: 10px;
            }}
        """)

    def lineNumberAreaWidth(self):
        digits = 1
        max_count = max(1, self.blockCount())
        while max_count >= 10:
            max_count /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2A2A2A"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#5C6370"))
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlightCurrentLine(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2A2A2A")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event):
        # 优先处理标准快捷键，确保不阻断默认行为
        standard_sequences = [
            QKeySequence.StandardKey.Copy,
            QKeySequence.StandardKey.Paste,
            QKeySequence.StandardKey.Undo,
            QKeySequence.StandardKey.Redo,
            QKeySequence.StandardKey.SelectAll,
            QKeySequence.StandardKey.Save,
            QKeySequence.StandardKey.Delete,
            QKeySequence.StandardKey.Backspace,
            QKeySequence.StandardKey.Cut,
        ]

        for seq in standard_sequences:
            if event.matches(seq):
                super().keyPressEvent(event)
                return

        cursor = self.textCursor()

        if event.matches(QKeySequence.StandardKey.Comment):
            self.toggle_comment()
            return

        if event.key() == Qt.Key.Key_D and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.duplicate_line()
            return

        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("  ")
            return

        pairs = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}
        if event.text() in pairs:
            self.insertPlainText(event.text() + pairs[event.text()])
            cursor.movePosition(cursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return

        super().keyPressEvent(event)

    def toggle_comment(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start, cursor.MoveMode.MoveAnchor)
        cursor.movePosition(cursor.MoveOperation.StartOfBlock, cursor.MoveMode.MoveAnchor)
        start_line_pos = cursor.position()
        cursor.setPosition(end, cursor.MoveMode.MoveAnchor)
        cursor.movePosition(cursor.MoveOperation.EndOfBlock, cursor.MoveMode.MoveAnchor)
        end_line_pos = cursor.position()

        cursor.setPosition(start_line_pos)
        cursor.beginEditBlock()
        while cursor.position() < end_line_pos:
            cursor.movePosition(cursor.MoveOperation.StartOfBlock)
            line_text = cursor.block().text().lstrip()
            if line_text.startswith('//'):
                cursor.movePosition(cursor.MoveOperation.Right, n=line_text.find('//'))
                cursor.deleteChar()
                cursor.deleteChar()
            else:
                self.insertPlainText('//')
            if not cursor.movePosition(cursor.MoveOperation.NextBlock):
                break
        cursor.endEditBlock()

    def duplicate_line(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(cursor.MoveOperation.StartOfBlock)
        cursor.movePosition(cursor.MoveOperation.EndOfBlock, cursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText()
        cursor.clearSelection()
        cursor.insertText(line_text + '\n' + line_text)
        cursor.endEditBlock()

    def open_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.setPlainText(f.read())
            self.current_file_path = file_path
        except Exception as e:
            self.setPlainText(f"Error opening file: {e}")

    def save_file(self):
        if hasattr(self, 'current_file_path') and self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.toPlainText())
                self.document().setModified(False)
            except Exception as e:
                print(f"Error saving file: {e}")

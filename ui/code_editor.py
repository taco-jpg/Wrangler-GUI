
from PySide6.QtCore import Qt, QRect, QSize, QRegularExpression
from PySide6.QtWidgets import QWidget, QPlainTextEdit
from PySide6.QtGui import QPainter, QColor, QSyntaxHighlighter, QTextCharFormat, QFont

class LineNumberArea(QWidget):
    """用于显示行号的侧边栏小部件。"""
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """带有行号和语法高亮的文本编辑器。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.current_file_path = None
        self.highlighter = JavaScriptHighlighter(self.document())

        # 连接信号和槽
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)


        self.update_line_number_area_width(0)


    def line_number_area_width(self):
        """计算行号区域所需的宽度。"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1
        
        # 根据字体和数字位数计算宽度，并添加一些边距
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits + 3
        return space

    def update_line_number_area_width(self, _):
        """当块数（行数）改变时，调整行号区域的边距。"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """当编辑器滚动时，同步滚动行号区域。"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """在编辑器大小改变时，重新定位行号区域。"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))



    def line_number_area_paint_event(self, event):
        """绘制行号区域的内容。"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2a2a2a")) # 设置背景色

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585")) # 设置行号颜色
                painter.drawText(0, int(top), self.line_number_area.width() - 5, int(self.fontMetrics().height()),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def open_file(self, file_path):
        """打开一个新文件并加载其内容。"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.setPlainText(f.read())
                self.current_file_path = file_path
        except Exception as e:
            self.setPlainText(f"Error opening file: {e}")
            self.current_file_path = None

    def save_file(self):
        """保存当前文件的内容。"""
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.toPlainText())
            except Exception as e:
                # 在状态栏或通过对话框显示错误会更好
                print(f"Error saving file: {e}")

class JavaScriptHighlighter(QSyntaxHighlighter):
    """一个简单的 JavaScript 语法高亮器。"""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []

        # 关键字
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c586c0")) # 紫色
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["\\bbreak\\b", "\\bcase\\b", "\\bcatch\\b", "\\bcontinue\\b", 
                    "\\bdebugger\\b", "\\bdefault\\b", "\\bdelete\\b", "\\bdo\\b", 
                    "\\belse\\b", "\\bfinally\\b", "\\bfor\\b", "\\bfunction\\b", 
                    "\\bif\\b", "\\bin\\b", "\\binstanceof\\b", "\\bnew\\b", 
                    "\\breturn\\b", "\\bswitch\\b", "\\bthis\\b", "\\bthrow\\b", 
                    "\\btry\\b", "\\btypeof\\b", "\\bvar\\b", "\\bvoid\\b", 
                    "\\bwhile\\b", "\\bwith\\b", "\\blet\\b", "\\bconst\\b", 
                    "\\bimport\\b", "\\bexport\\b", "\\bclass\\b", "\\bextends\\b", 
                    "\\bsuper\\b", "\\basync\\b", "\\bawait\\b"]
        for word in keywords:
            pattern = QRegularExpression(word)
            self.highlighting_rules.append((pattern, keyword_format))

        # 单行注释
        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor("#6A9955")) # 绿色
        self.highlighting_rules.append((QRegularExpression("//[^\n]*"), single_line_comment_format))

        # 字符串
        quotation_format = QTextCharFormat()
        quotation_format.setForeground(QColor("#ce9178")) # 橙色
        self.highlighting_rules.append((QRegularExpression('".*"'), quotation_format))
        self.highlighting_rules.append((QRegularExpression("'.*'"), quotation_format))

        # 函数名
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA")) # 淡黄色
        self.highlighting_rules.append((QRegularExpression("\\b[A-Za-z0-9_]+(?=\\()"), function_format))

    def highlightBlock(self, text):
        """对文本块应用高亮规则。"""
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

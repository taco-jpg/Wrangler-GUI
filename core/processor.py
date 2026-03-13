
import re
import json
from PySide6.QtCore import QObject, Signal, QProcess

def ansi_to_html(ansi_text):
    """
    将包含 ANSI 转义码的文本转换为 HTML。
    一个简化的实现，用于处理常见的颜色代码。
    """
    color_map = {
        '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
        '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
        '90': 'grey'
    }
    
    # 将换行符替换为 <br>
    html_text = ansi_text.replace('\n', '<br>')

    # 正则表达式匹配 ANSI 颜色代码
    ansi_escape_pattern = re.compile(r'\x1B\[([0-9;]+)m')

    parts = []
    last_end = 0
    is_open = False

    for match in ansi_escape_pattern.finditer(html_text):
        start, end = match.span()
        parts.append(html_text[last_end:start])
        last_end = end
        
        codes = match.group(1).split(';')
        
        if is_open:
            parts.append('</span>')
            is_open = False

        # 我们只处理简单的颜色代码，忽略粗体、下划线等
        color_code = codes[0]
        if color_code in color_map:
            color = color_map[color_code]
            parts.append(f'<span style="color:{color};">')
            is_open = True
        elif color_code == '0': # 重置
            # 已经在前面关闭了 span，所以这里什么都不做
            pass

    parts.append(html_text[last_end:])
    if is_open:
        parts.append('</span>')

    return "".join(parts)


class CommandManager(QObject):
    """
    封装 QProcess 用于执行和管理外部命令（如 wrangler）。
    """
    # 信号定义
    output_received = Signal(str)       # 发送原始或处理后的输出
    json_received = Signal(dict)        # 发送解析后的JSON对象
    error_detected = Signal()           # 当在stderr中检测到错误时发出
    process_started = Signal()          # 进程开始时发出
    process_finished = Signal(int, QProcess.ExitStatus) # 进程结束时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._buffer = ""
        self._setup_signals()

    def _setup_signals(self):
        """连接 QProcess 的信号到内部槽函数。"""
        self._process.readyReadStandardOutput.connect(self._on_ready_read_stdout)
        self._process.readyReadStandardError.connect(self._on_ready_read_stderr)
        self._process.started.connect(self.process_started)
        self._process.finished.connect(self.process_finished)

    def _on_ready_read_stdout(self):
        """处理标准输出，尝试将其解析为JSON。"""
        data = self._process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self._buffer += data

        # wrangler --json 模式下，每行都是一个独立的JSON对象
        lines = self._buffer.split('\n')
        self._buffer = lines.pop()  # 保留最后一行不完整的JSON

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse as JSON only if it looks like JSON
            if line.startswith('{') or line.startswith('['):
                try:
                    json_data = json.loads(line)
                    self.json_received.emit(json_data)
                    continue  # Successfully parsed, move to the next line
                except json.JSONDecodeError:
                    # It looked like JSON but failed to parse, so treat as regular text.
                    pass
            
            # If it's not JSON or failed to parse, treat as regular text output
            html_output = ansi_to_html(line + '\n')
            self.output_received.emit(html_output)

    def _on_ready_read_stderr(self):
        """处理标准错误输出。"""
        data = self._process.readAllStandardError().data().decode('utf-8', errors='ignore')
        # 检查是否包含错误关键字
        if 'error' in data.lower():
            self.error_detected.emit()

        # 错误输出也转换为HTML，通常它们也包含颜色代码
        html_output = ansi_to_html(data)
        self.output_received.emit(f'<span style="color:red;">{html_output}</span>')

    def execute(self, command, args=None, working_directory=None, stdin=None):
        """
        执行一个新命令。
        :param command: 要执行的命令 (e.g., "wrangler")。
        :param args: 命令的参数列表 (e.g., ["dev"])。
        """
        if args is None:
            args = []
        
        if self.is_running():
            # 如果已有进程在运行，可以选择停止它或发出警告
            # 在这里我们先停止旧的
            self.stop()
            # 等待一小段时间确保进程已停止
            self._process.waitForFinished(1000)

        # 设置工作目录
        if working_directory:
            self._process.setWorkingDirectory(working_directory)
        else:
            # 如果未提供，则使用默认行为（通常是当前应用的目录）
            self._process.setWorkingDirectory("")

        self._process.start(command, args)

        if stdin:
            self._process.write(stdin.encode('utf-8'))
            self._process.closeWriteChannel()

    def stop(self):
        """停止当前正在运行的进程。"""
        if self.is_running():
            self._process.kill()
            self.output_received.emit('<br><span style="color:yellow;">[Process stopped by user]</span><br>')

    def is_running(self):
        """检查是否有进程正在运行。"""
        return self._process.state() != QProcess.NotRunning

    def write_to_process(self, data: str):
        """向正在运行的进程写入数据（用于交互式命令）。"""
        if self.is_running():
            self._process.write(data.encode('utf-8'))


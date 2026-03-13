import os
from PySide6.QtWidgets import QFileIconProvider, QApplication, QStyle
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFileInfo

class FileIconProvider(QFileIconProvider):
    """为特定的文件类型提供自定义的 Qt 内置图标。"""

    def icon(self, fileInfo):
        """根据文件类型返回一个 QStyle.StandardPixmap 图标。"""
        if fileInfo.isDir():
            return QApplication.style().standardIcon(QStyle.SP_DirIcon)

        if fileInfo.fileName().endswith('.js') or fileInfo.fileName() == 'wrangler.toml':
            return QApplication.style().standardIcon(QStyle.SP_FileIcon)
        
        # 对于所有其他文件，也使用标准文件图标
        return QApplication.style().standardIcon(QStyle.SP_FileIcon)

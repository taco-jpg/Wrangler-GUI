
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QSplitter, QLabel, QFileDialog,
    QTreeView, QPlainTextEdit, QToolBar, QTabWidget, QProgressBar, QDockWidget, QStatusBar, QSystemTrayIcon, QGraphicsDropShadowEffect, QStackedWidget, QFileSystemModel, QInputDialog, QMessageBox, QStyle, QApplication
)
from PySide6.QtGui import QFont, QAction, QMovie, QIcon, QColor
from PySide6.QtCore import Qt, Slot, QProcess, QPropertyAnimation, QEasingCurve, QSize
from ui.code_editor import CodeEditor
from ui.settings_panel import SettingsPanel
from ui.icon_provider import FileIconProvider
from ui.animated_button import AnimatedButton
from ui.breathing_dot import BreathingDot
from ui.welcome_screen import WelcomeScreen
from ui.dock_title_bar import DockTitleBar

from core.processor import CommandManager

class MainWindow(QMainWindow):
    """主窗口类，包含应用的所有UI元素和信号连接。"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Wrangler-Desktop")
        self.setGeometry(100, 100, 1200, 800)

        # 初始化命令管理器
        self.command_manager = CommandManager(self)
        self.current_project_path = None

        # 设置UI
        self._setup_ui()
        # 连接信号和槽
        self._setup_signals()

    def _setup_ui(self):
        """初始化和布局所有UI组件。"""
        # --- 创建主编辑器界面 ---
        editor_widget = self._create_editor_widget()

        # --- 创建欢迎界面 ---
        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.open_project_requested.connect(self._on_open_project)

        # --- 创建堆叠窗口用于切换 ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(editor_widget)

        self.setCentralWidget(self.stacked_widget)

        # --- 设置其他UI元素（工具栏、状态栏等） ---
        self._setup_toolbar()
        self._setup_tray_icon()
        self._setup_log_dock()
        self._setup_status_bar()

    def _create_editor_widget(self):
        """创建并返回主编辑器界面的主控件。"""
        # 主分割器，左右布局
        main_splitter = QSplitter(Qt.Horizontal, self)

        # --- 左侧：文件浏览器 ---
        file_browser_widget = QWidget()
        file_browser_layout = QVBoxLayout(file_browser_widget)
        file_browser_layout.setContentsMargins(0, 0, 0, 0)
        file_browser_layout.setSpacing(0)

        # 文件浏览器工具栏
        file_toolbar = QToolBar("File Toolbar")
        file_toolbar.setIconSize(QSize(16, 16))

        style = QApplication.style()
        new_file_action = QAction("New File", self) # 使用文字按钮
        new_folder_action = QAction(style.standardIcon(QStyle.SP_FileDialogNewFolder), "New Folder", self)
        refresh_action = QAction(style.standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        delete_action = QAction(style.standardIcon(QStyle.SP_TrashIcon), "Delete", self)

        new_file_action.triggered.connect(self._on_new_file)
        new_folder_action.triggered.connect(self._on_new_folder)
        refresh_action.triggered.connect(self._on_refresh)
        delete_action.triggered.connect(self._on_delete)

        file_toolbar.addAction(new_file_action)
        file_toolbar.addAction(new_folder_action)
        file_toolbar.addAction(refresh_action)
        file_toolbar.addAction(delete_action)

        self.file_tree_view = QTreeView()
        self.file_tree_view.setHeaderHidden(True)

        file_browser_layout.addWidget(file_toolbar)
        file_browser_layout.addWidget(self.file_tree_view)

        # --- 右上：标签页（编辑器和设置） ---
        self.tab_widget = QTabWidget()
        
        # 代码编辑器
        self.code_editor = CodeEditor()
        self.code_editor.setPlaceholderText("Select a file to edit...")

        # 设置面板
        self.settings_panel = SettingsPanel()

        self.tab_widget.addTab(self.code_editor, "Editor")
        self.tab_widget.addTab(self.settings_panel, "Settings")

        # 组装分割器
        main_splitter.addWidget(file_browser_widget)
        main_splitter.addWidget(self.tab_widget)
        main_splitter.setSizes([250, 950])

        return main_splitter

    def _setup_toolbar(self):
        """设置工具栏。"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        open_project_action = QAction("Open Project", self)
        open_project_action.triggered.connect(self._on_open_project)
        toolbar.addAction(open_project_action)

        toolbar.addSeparator()

        # 部署按钮
        self.deploy_button = AnimatedButton("Deploy")
        self.deploy_button.clicked.connect(self._on_deploy)
        toolbar.addWidget(self.deploy_button)

        # 停止按钮
        self.stop_button = AnimatedButton("Stop")
        self.stop_button.clicked.connect(self.command_manager.stop)
        toolbar.addWidget(self.stop_button)

        # 部署进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        toolbar.addWidget(self.progress_bar)

        # 初始隐藏项目相关控件
        self.deploy_button.hide()
        self.stop_button.hide()
        self.progress_bar.hide()
        self.stop_button.setEnabled(False)

    def _setup_tray_icon(self):
        """设置系统托盘图标。"""
        self.tray_icon = QSystemTrayIcon(self)
        tray_icon_image = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(tray_icon_image)
        self.tray_icon.setVisible(True)

    def _setup_log_dock(self):
        """设置可停靠的日志面板。"""
        self.log_dock_widget = QDockWidget("Logs", self)
        self.log_dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        # 创建并设置自定义标题栏
        self.dock_title_bar = DockTitleBar("Logs")
        self.dock_title_bar.kill_process_requested.connect(self.command_manager.stop)
        self.dock_title_bar.hide_button.clicked.connect(self.log_dock_widget.hide)
        self.log_dock_widget.setTitleBarWidget(self.dock_title_bar)

        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setPlaceholderText("Logs will appear here...")
        self.log_dock_widget.setWidget(self.log_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock_widget)
        self.log_dock_widget.setVisible(False) # 默认隐藏

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, -2)
        self.log_dock_widget.setGraphicsEffect(shadow)

    def _setup_status_bar(self):
        """设置状态栏。"""
        self.setStatusBar(QStatusBar(self))
        self.status_label = QLabel("Ready")
        self.status_animation = BreathingDot()
        self.statusBar().addPermanentWidget(self.status_animation)
        self.statusBar().addPermanentWidget(self.status_label)
        self.status_animation.hide()

        self._setup_shortcuts()

    def _setup_file_system_model(self, project_path):
        """设置文件系统模型并应用到 QTreeView。"""
        self.fs_model = QFileSystemModel()
        self.fs_model.setIconProvider(FileIconProvider()) # 设置自定义图标
        self.fs_model.setRootPath(project_path)
        self.file_tree_view.setModel(self.fs_model)
        self.file_tree_view.setRootIndex(self.fs_model.index(project_path))

        # 隐藏不必要的列
        for i in range(1, self.fs_model.columnCount()):
            self.file_tree_view.hideColumn(i)

    @Slot()
    def _on_open_project(self):
        """处理打开项目按钮点击事件。"""
        project_path = QFileDialog.getExistingDirectory(
            self,
            "Select Your Cloudflare Worker Project Directory",
            os.path.expanduser("~")
        )
        if project_path:
            self.current_project_path = project_path
            self._setup_file_system_model(project_path)
            self.settings_panel.set_project(project_path)
            
            # 切换到编辑器界面并显示相关控件
            self.stacked_widget.setCurrentIndex(1)
            self.deploy_button.show()
            self.stop_button.show()
            self.progress_bar.show()

    @Slot(dict)
    def _on_json_received(self, data):
        """处理来自命令的JSON输出。"""
        log_type = data.get('type')
        if log_type == 'progress':
            stage = data.get('stage')
            percentage = int(data.get('percentage', 0) * 100)
            
            # 使用动画平滑更新进度条
            self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
            self.progress_animation.setDuration(250) # 动画时长250ms
            self.progress_animation.setStartValue(self.progress_bar.value())
            self.progress_animation.setEndValue(percentage)
            self.progress_animation.setEasingCurve(QEasingCurve.InOutCubic)
            self.progress_animation.start()

            self.progress_bar.setFormat(f"{stage}: {percentage}%")
        else:
            # 其他类型的JSON日志，直接打印到日志面板
            self.log_panel.appendPlainText(str(data))

    @Slot()
    def _on_deploy(self):
        """处理部署按钮点击事件。"""
        if not self.current_project_path:
            self.log_panel.appendPlainText("Error: No project opened.")
            return

        self.log_panel.clear()
        self.log_panel.appendPlainText("Starting deployment...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.deploy_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._toggle_log_panel_animation(show=True)

        # 更新状态栏
        self.status_label.setText("Deploying...")
        self.status_animation.start()

        # 使用 --json 和 --yes 参数
        self.command_manager.execute(
            "wrangler", 
            ["deploy", "--json", "--yes"], 
            working_directory=self.current_project_path
        )



    @Slot()
    def _on_new_file(self):
        """处理新建文件请求。"""
        index = self.file_tree_view.currentIndex()
        if not index.isValid():
            return

        dir_path = self.fs_model.filePath(index) if self.fs_model.isDir(index) else os.path.dirname(self.fs_model.filePath(index))
        
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(dir_path, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write('')
            else:
                QMessageBox.warning(self, "Warning", "File already exists.")

    @Slot()
    def _on_new_folder(self):
        """处理新建文件夹请求。"""
        index = self.file_tree_view.currentIndex()
        if not index.isValid():
            return

        dir_path = self.fs_model.filePath(index) if self.fs_model.isDir(index) else os.path.dirname(self.fs_model.filePath(index))

        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            folder_path = os.path.join(dir_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            else:
                QMessageBox.warning(self, "Warning", "Folder already exists.")

    @Slot()
    def _on_refresh(self):
        """刷新文件树。"""
        # QFileSystemModel 通常会自动更新，但可以手动触发
        self.fs_model.setRootPath(self.current_project_path) # 重新设置根路径以强制刷新
        self.file_tree_view.setRootIndex(self.fs_model.index(self.current_project_path))

    @Slot()
    def _on_delete(self):
        """处理删除文件或文件夹请求。"""
        index = self.file_tree_view.currentIndex()
        if not index.isValid():
            return

        file_path = self.fs_model.filePath(index)
        reply = QMessageBox.question(self, 'Delete', f"Are you sure you want to delete \n'{file_path}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                if self.fs_model.isDir(index):
                    os.rmdir(file_path) # 注意：os.rmdir 只能删除空目录
                else:
                    os.remove(file_path)
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    @Slot()
    def _on_login(self):
        """处理登录请求。"""
        self.log_panel.clear()
        self.log_panel.appendPlainText("Starting login process...")
        self._toggle_log_panel_animation(show=True)
        self.status_label.setText("Logging in...")
        self.status_animation.start()
        self.command_manager.execute("wrangler", ["login"])

    @Slot()
    def _on_logout(self):
        """处理登出请求。"""
        self.log_panel.clear()
        self.log_panel.appendPlainText("Starting logout process...")
        self._toggle_log_panel_animation(show=True)
        self.status_label.setText("Logging out...")
        self.status_animation.start()
        self.command_manager.execute("wrangler", ["logout"])

    @Slot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code, exit_status):
        """进程结束后，在终端显示状态信息。"""
        self.status_animation.stop()

        if exit_status == QProcess.NormalExit and exit_code == 0:
            self.status_label.setText("Success")
            self.log_panel.appendPlainText("Process finished successfully.")
            self.tray_icon.showMessage("Deployment Successful", "Your project has been deployed successfully.", QSystemTrayIcon.Information, 3000)
        else:
            self.status_label.setText("Failed")
            self.log_panel.appendPlainText(f'Process crashed or failed with exit code: {exit_code}.')
            self.tray_icon.showMessage("Deployment Failed", f"The process failed with exit code {exit_code}.", QSystemTrayIcon.Critical, 3000)
        
        self.progress_bar.setVisible(False)
        self.deploy_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    @Slot()
    def _on_error_detected(self):
        """当检测到错误时，确保日志面板是可见的。"""
        self._toggle_log_panel_animation(show=True)

    def _toggle_log_panel_animation(self, show: bool):
        """使用动画显示或隐藏日志面板。"""
        if show and self.log_dock_widget.isHidden():
            self.log_dock_widget.show()
            self.animation = QPropertyAnimation(self.log_dock_widget, b"maximumHeight")
            self.animation.setDuration(300) # 动画时长300ms
            self.animation.setStartValue(0)
            self.animation.setEndValue(300)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.start()
        elif not show and not self.log_dock_widget.isHidden():
            self.animation = QPropertyAnimation(self.log_dock_widget, b"maximumHeight")
            self.animation.setDuration(300)
            self.animation.setStartValue(300)
            self.animation.setEndValue(0)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.finished.connect(self.log_dock_widget.hide)
            self.animation.start()

    @Slot(str)
    def _on_output_received(self, text):
        """处理来自命令的原始文本输出。"""
        # Wrangler's --json flag can still print non-json text to stdout,
        # so we'll append it to the log for debugging.
        self.log_panel.appendPlainText(text)

    @Slot('QModelIndex')
    def _on_file_tree_double_clicked(self, index):
        """处理文件树中的双击事件。"""
        file_path = self.fs_model.filePath(index)
        if not self.fs_model.isDir(index):
            self.code_editor.open_file(file_path)



    def _setup_signals(self):
        """连接所有信号和槽。"""
        # 命令管理器信号
        self.command_manager.output_received.connect(self._on_output_received)
        self.command_manager.process_finished.connect(self._on_process_finished)
        self.command_manager.json_received.connect(self._on_json_received)
        self.command_manager.error_detected.connect(self._on_error_detected)

        # UI 按钮信号
        self.file_tree_view.doubleClicked.connect(self._on_file_tree_double_clicked)

        # 设置面板信号
        self.settings_panel.login_requested.connect(self._on_login)
        self.settings_panel.logout_requested.connect(self._on_logout)





    def closeEvent(self, event):
        """关闭窗口前，确保停止所有正在运行的进程。"""
        self.command_manager.stop()
        super().closeEvent(event)


    def _setup_shortcuts(self):
        """设置全局的键盘快捷键。"""
        from PySide6.QtGui import QShortcut, QKeySequence
        # 保存文件
        save_shortcut = QShortcut(QKeySequence.Save, self)
        save_shortcut.activated.connect(self._on_save_file)

        # 打开项目
        open_shortcut = QShortcut(QKeySequence.Open, self)
        open_shortcut.activated.connect(self._on_open_project)

        # 关闭标签页
        close_tab_shortcut = QShortcut(QKeySequence("Cmd+W"), self)
        close_tab_shortcut.activated.connect(self._on_close_tab)

    @Slot()
    def _on_save_file(self):
        """保存当前打开的文件。"""
        # 假设 code_editor 有一个 save_file 的方法
        if hasattr(self.code_editor, 'save_file') and self.code_editor.current_file_path:
            self.code_editor.save_file()
            self.status_label.setText(f"Saved {os.path.basename(self.code_editor.current_file_path)}")

    @Slot()
    def _on_close_tab(self):
        """关闭当前的编辑器标签页。"""
        current_index = self.tab_widget.currentIndex()
        # 确保我们不会关闭设置标签页
        if self.tab_widget.tabText(current_index) != "Settings":
            self.tab_widget.removeTab(current_index)


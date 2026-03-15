import html
import json
import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QProgressBar, QDockWidget, QStatusBar, QSystemTrayIcon,
    QGraphicsDropShadowEffect, QStackedWidget, QFileSystemModel,
    QInputDialog, QMessageBox, QStyle, QApplication, QTabWidget, QSizePolicy, QToolButton, QTreeView, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QLineEdit, QPlainTextEdit, QFileDialog, QMenu, QLabel, QPushButton, QTableWidget, QHeaderView, QDialog, QDialogButtonBox, QFormLayout, QVBoxLayout
)
from PySide6.QtGui import (
    QFont, QAction, QIcon, QColor, QKeySequence, QDesktopServices, QShortcut, QTextCursor
)
from PySide6.QtCore import Qt, Slot, QProcess, QPropertyAnimation, QEasingCurve, QSize, QPoint, QUrl, QDir, QSettings, QModelIndex, QTimer

from .theme import COLORS, get_font
from .code_editor import CodeEditor
from .settings_panel import SettingsPanel
from .breathing_dot import BreathingDot
from .terminal import Terminal
from .animations import apply_pulse_animation
from .animated_button import AnimatedButton
from core.processor import CommandManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (rest of __init__ as before)
        self.setWindowTitle("Wrangler-Desktop")
        self.setGeometry(100, 100, 1200, 800)
        self.main_command_manager = CommandManager(self, raw_output=False)
        self.tail_command_manager = CommandManager(self, raw_output=True)
        self.versions_command_manager = CommandManager(self, raw_output=False)
        self.kv_command_manager = CommandManager(self, raw_output=False)
        self.current_project_path = None
        self.open_files = {}
        self.is_dev_mode = False
        self.is_tailing = False
        self.pending_versions_reload = False
        self.current_kv_namespace_id = None
        self.waiting_for_kv_keys = False
        self.save_action = None
        self.back_action = None
        self.forward_action = None
        self.current_editor = None
        self._setup_ui()
        self._setup_styles()
        self._setup_signals()
        self._setup_shortcuts()

    # ... (UI setup methods as before) ...
    def _setup_ui(self):
        self._setup_file_system_dock()
        editor_widget = self._create_editor_widget()
        self.setCentralWidget(editor_widget)
        self._setup_toolbar()
        self._setup_tray_icon()
        self._setup_status_bar()
        self._setup_log_dock()
        self._setup_versions_dock()

    def _setup_file_system_dock(self):
        self.file_system_dock = QDockWidget("Project", self)
        self.file_system_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        toolbar = self._create_file_tree_toolbar()
        self.file_tree_view = QTreeView()
        container_layout.addWidget(toolbar)
        container_layout.addWidget(self.file_tree_view)

        # KV Namespaces section
        self.kv_tree_widget = QTreeWidget()
        self.kv_tree_widget.setHeaderLabel("KV Namespaces")
        self.kv_tree_widget.setMaximumHeight(300)
        self.kv_tree_widget.setMinimumHeight(100)
        self.kv_namespaces_root = QTreeWidgetItem(self.kv_tree_widget, ["KV Namespaces"])
        self.kv_namespaces_root.setExpanded(False)
        self.kv_tree_widget.itemExpanded.connect(self._on_kv_namespace_expanded)
        container_layout.addWidget(self.kv_tree_widget)

        self.file_system_dock.setWidget(container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_system_dock)

    def _create_file_tree_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)

        new_file_button = QToolButton()
        new_file_button.setText("New File")
        new_file_button.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 4px;")
        new_file_button.clicked.connect(self._on_new_file)
        toolbar.addWidget(new_file_button)

        # Save button
        self.save_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "Save", self)
        self.save_action.triggered.connect(self._on_save_file)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.setEnabled(False)  # Initially disabled until a file is opened
        toolbar.addAction(self.save_action)

        # Back (Undo) button
        self.back_action = QAction(self.style().standardIcon(QStyle.SP_ArrowBack), "Undo", self)
        self.back_action.triggered.connect(self._on_back_clicked)
        self.back_action.setEnabled(False)
        toolbar.addAction(self.back_action)

        # Forward (Redo) button
        self.forward_action = QAction(self.style().standardIcon(QStyle.SP_ArrowForward), "Redo", self)
        self.forward_action.triggered.connect(self._on_forward_clicked)
        self.forward_action.setEnabled(False)
        toolbar.addAction(self.forward_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        new_folder_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "New Folder", self)
        new_folder_action.triggered.connect(self._on_new_folder)
        toolbar.addAction(new_folder_action)

        refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)

        delete_action = QAction(self.style().standardIcon(QStyle.SP_TrashIcon), "Delete", self)
        delete_action.triggered.connect(self._on_delete)
        toolbar.addAction(delete_action)
        return toolbar

    def _create_editor_widget(self):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.settings_panel = SettingsPanel(command_manager=self.main_command_manager)
        self.editor_tabs.addTab(self.settings_panel, "Settings")

        # KV Browser 标签页（初始隐藏）
        self.kv_browser_widget = QWidget()
        kv_browser_layout = QHBoxLayout(self.kv_browser_widget)
        kv_browser_layout.setContentsMargins(0, 0, 0, 0)
        kv_browser_layout.setSpacing(10)

        # 左侧：key 列表和搜索框
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏按钮
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.kv_new_key_button = QPushButton("New Key")
        self.kv_new_key_button.clicked.connect(self._on_kv_new_key)
        toolbar_layout.addWidget(self.kv_new_key_button)
        self.kv_delete_key_button = QPushButton("Delete Key")
        self.kv_delete_key_button.clicked.connect(self._on_kv_delete_key)
        toolbar_layout.addWidget(self.kv_delete_key_button)
        self.kv_refresh_button = QPushButton("Refresh")
        self.kv_refresh_button.clicked.connect(self._on_kv_refresh)
        toolbar_layout.addWidget(self.kv_refresh_button)
        left_layout.addWidget(toolbar_widget)

        self.kv_search_box = QLineEdit()
        self.kv_search_box.setPlaceholderText("Search keys...")
        self.kv_search_box.textChanged.connect(self._on_kv_search_text_changed)
        left_layout.addWidget(self.kv_search_box)
        self.kv_key_list = QListWidget()
        self.kv_key_list.currentItemChanged.connect(self._on_kv_key_selected)
        left_layout.addWidget(self.kv_key_list)
        kv_browser_layout.addWidget(left_widget)

        # 右侧：value 预览
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.kv_value_preview = QPlainTextEdit()
        self.kv_value_preview.setReadOnly(True)
        right_layout.addWidget(self.kv_value_preview)
        kv_browser_layout.addWidget(right_widget)

        self.kv_browser_tab_index = self.editor_tabs.addTab(self.kv_browser_widget, "KV Browser")
        self.editor_tabs.setTabVisible(self.kv_browser_tab_index, False)
        return self.editor_tabs

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.deploy_button = AnimatedButton("Deploy", button_type='primary')
        self.deploy_button.clicked.connect(self._on_deploy)
        toolbar.addWidget(self.deploy_button)
        # Versions button
        self.versions_button = QPushButton("Versions")
        self.versions_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #F6821F;
                border: 1px solid #F6821F;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #FFF3E8;
            }
            QPushButton:pressed {
                background-color: #FFE0C2;
            }
        """)
        self.versions_button.clicked.connect(self._on_versions_clicked)
        toolbar.addWidget(self.versions_button)
        self.dev_button = AnimatedButton("Dev", button_type='secondary')
        self.dev_button.clicked.connect(self._on_dev)
        toolbar.addWidget(self.dev_button)
        self.stop_button = AnimatedButton("Stop", button_type='outline')
        self.stop_button.clicked.connect(self.main_command_manager.stop)
        toolbar.addWidget(self.stop_button)
        self.deploy_button.hide()
        self.dev_button.hide()
        self.stop_button.hide()
        self.versions_button.hide()

        self.open_action = QAction("Open Project", self)
        self.open_action.triggered.connect(self._on_open_project)
        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(self.close)

    def _setup_log_dock(self):
        self.log_dock_widget = QDockWidget("Output", self)
        self.log_dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        log_title_bar = QToolBar()
        log_title_bar.setMovable(False)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.tail_button = AnimatedButton("Tail", button_type='outline')
        log_title_bar.addWidget(spacer)
        log_title_bar.addWidget(self.tail_button)
        # Add close button
        close_action = QAction(self.style().standardIcon(QStyle.SP_TitleBarCloseButton), "Close", self)
        close_action.triggered.connect(self.log_dock_widget.hide)
        log_title_bar.addAction(close_action)
        self.log_dock_widget.setTitleBarWidget(log_title_bar)
        self.output_tabs = QTabWidget()
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        self.output_tabs.addTab(self.log_panel, "Logs")
        self.log_dock_widget.setWidget(self.output_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock_widget)
        self.log_dock_widget.hide()
        # Set fixed height
        self.log_dock_widget.setMaximumHeight(200)
        self.log_dock_widget.setMinimumHeight(200)

    def _setup_versions_dock(self):
        """设置版本历史面板。"""
        self.versions_dock_widget = QDockWidget("Deployment History", self)
        self.versions_dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.versions_dock_widget.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

        # 创建表格
        self.versions_table = QTableWidget()
        self.versions_table.setColumnCount(4)
        self.versions_table.setHorizontalHeaderLabels(["Version ID", "Time", "Status", "Actions"])
        self.versions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.versions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.versions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.versions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.versions_table.verticalHeader().setVisible(False)
        self.versions_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置表格样式
        self.versions_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: transparent;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)

        self.versions_dock_widget.setWidget(self.versions_table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.versions_dock_widget)
        self.versions_dock_widget.hide()

    def _setup_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {COLORS["BACKGROUND_PRIMARY"].name()}; }}
            QDockWidget {{ titlebar-close-icon: none; }}
        """)

    def _setup_tray_icon(self):
        # 尝试加载图标资源，如果失败则使用默认图标
        icon = QIcon(":/icons/wrangler-icon.png")
        if icon.isNull():
            # 使用默认图标
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Wrangler Desktop")
        tray_menu = QMenu()
        tray_menu.addAction(self.open_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { height: 28px; }")
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_animation = BreathingDot()
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(8, 0, 8, 0)
        status_layout.addWidget(self.status_animation)
        status_layout.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(status_widget)
        # Initialize animation state
        self.status_animation.set_state('idle')

    def _setup_shortcuts(self):
        QShortcut(QKeySequence.Open, self, self._on_open_project)
        QShortcut(QKeySequence("Ctrl+O"), self, self._on_open_project)
        QShortcut(QKeySequence.Save, self, self._on_save_file)
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_save_file)

    def _setup_file_system_model(self, project_path):
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(project_path)
        self.file_tree_view.setModel(self.file_system_model)
        root_index = self.file_system_model.index(project_path)
        self.file_tree_view.setRootIndex(root_index)

    def _open_file(self, file_path):
        if file_path in self.open_files:
            self.editor_tabs.setCurrentWidget(self.open_files[file_path])
            return

        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {e}")
            return

        editor = CodeEditor()
        editor.setPlainText(content)
        editor.file_path = file_path
        index = self.editor_tabs.addTab(editor, os.path.basename(file_path))
        self.editor_tabs.setCurrentIndex(index)
        self.open_files[file_path] = editor

    def _setup_signals(self):
        self.editor_tabs.tabCloseRequested.connect(self._on_close_tab)
        self.editor_tabs.currentChanged.connect(self._on_main_tab_changed)
        self.main_command_manager.output_received.connect(self._on_output_received)
        self.main_command_manager.process_finished.connect(self._on_process_finished)
        self.tail_command_manager.output_received.connect(self._on_tail_output_received)
        self.tail_button.clicked.connect(self._on_tail_clicked)
        self.versions_command_manager.json_received.connect(self._on_versions_loaded)
        self.versions_command_manager.output_received.connect(self._on_output_received)
        self.versions_command_manager.process_finished.connect(self._on_versions_process_finished)
        self.file_tree_view.doubleClicked.connect(self._on_file_tree_double_clicked)
        self.settings_panel.login_requested.connect(self._on_login)
        self.settings_panel.logout_requested.connect(self._on_logout)
        self.kv_command_manager.json_received.connect(self._on_kv_namespaces_loaded)
        self.kv_command_manager.output_received.connect(self._on_kv_output_received)
        self.kv_command_manager.process_finished.connect(self._on_kv_process_finished)
        self.kv_tree_widget.itemClicked.connect(self._on_kv_namespace_clicked)

    @Slot()
    def _on_save_file(self):
        current_widget = self.editor_tabs.currentWidget()
        if isinstance(current_widget, CodeEditor) and hasattr(current_widget, 'file_path'):
            try:
                current_widget.save_file()
                self.status_label.setText(f"Saved {os.path.basename(current_widget.file_path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {e}")

    @Slot()
    def _on_back_clicked(self):
        if self.current_editor:
            self.current_editor.undo()

    @Slot()
    def _on_forward_clicked(self):
        if self.current_editor:
            self.current_editor.redo()

    @Slot()
    def _on_editor_undo_available(self, available):
        if self.back_action:
            self.back_action.setEnabled(available)

    @Slot()
    def _on_editor_redo_available(self, available):
        if self.forward_action:
            self.forward_action.setEnabled(available)

    @Slot(bool)
    def _on_editor_modification_changed(self, changed):
        if self.save_action:
            self.save_action.setEnabled(changed)

    @Slot(int)
    def _on_close_tab(self, index):
        widget = self.editor_tabs.widget(index)
        if isinstance(widget, CodeEditor) and hasattr(widget, 'file_path'):
            del self.open_files[widget.file_path]
        # If closing the current editor, clean up
        if widget == self.current_editor:
            try:
                self.current_editor.undoAvailable.disconnect(self._on_editor_undo_available)
                self.current_editor.redoAvailable.disconnect(self._on_editor_redo_available)
                self.current_editor.modificationChanged.disconnect(self._on_editor_modification_changed)
            except:
                pass
            self.current_editor = None
            # Disable buttons
            if self.back_action:
                self.back_action.setEnabled(False)
            if self.forward_action:
                self.forward_action.setEnabled(False)
            if self.save_action:
                self.save_action.setEnabled(False)
        self.editor_tabs.removeTab(index)

    @Slot(int)
    def _on_main_tab_changed(self, index):
        widget = self.editor_tabs.widget(index)
        if widget == self.settings_panel:
            self.settings_panel.load_secrets()

        # Disconnect previous editor signals
        if self.current_editor:
            try:
                self.current_editor.undoAvailable.disconnect(self._on_editor_undo_available)
                self.current_editor.redoAvailable.disconnect(self._on_editor_redo_available)
                self.current_editor.modificationChanged.disconnect(self._on_editor_modification_changed)
            except:
                pass  # Not connected

        # Update current editor and connect signals
        from .code_editor import CodeEditor
        if isinstance(widget, CodeEditor):
            self.current_editor = widget
            self.current_editor.undoAvailable.connect(self._on_editor_undo_available)
            self.current_editor.redoAvailable.connect(self._on_editor_redo_available)
            self.current_editor.modificationChanged.connect(self._on_editor_modification_changed)
            # Update button states based on current editor
            # Initial state: buttons disabled, signals will update them
            self.back_action.setEnabled(False)
            self.forward_action.setEnabled(False)
            self.save_action.setEnabled(self.current_editor.document().isModified())
        else:
            self.current_editor = None
            # Disable buttons when no editor is active
            self.back_action.setEnabled(False)
            self.forward_action.setEnabled(False)
            self.save_action.setEnabled(False)

    @Slot(str)
    def _on_output_received(self, text):
        self.log_panel.appendHtml(text)
        self.log_panel.moveCursor(QTextCursor.End)

    @Slot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code, exit_status):
        if exit_status == QProcess.CrashExit:
            self.status_label.setText("Process crashed")
            self.status_animation.set_state('error')
        else:
            self.status_label.setText("Ready")
            self.status_animation.set_state('idle')
        self.stop_button.setEnabled(False)

    @Slot(QModelIndex)
    def _on_file_tree_double_clicked(self, index):
        file_path = self.file_system_model.filePath(index)
        if self.file_system_model.isDir(index):
            return
        self._open_file(file_path)

    @Slot()
    def _on_login(self):
        self.main_command_manager.execute("wrangler", ["login"])

    @Slot()
    def _on_logout(self):
        self.main_command_manager.execute("wrangler", ["logout"])

    def closeEvent(self, event):
        self.main_command_manager.stop()
        self.tail_command_manager.stop()
        self.versions_command_manager.stop()
        super().closeEvent(event)

    def open_project(self, project_path):
        self.current_project_path = project_path
        self._setup_file_system_model(project_path)
        self.settings_panel.set_project(project_path)
        self.deploy_button.show()
        self.dev_button.show()
        self.stop_button.show()
        self.versions_button.show()

    @Slot()
    def _on_open_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "Open Project", QDir.homePath())
        if project_path:
            settings = QSettings("WranglerGUI", "WranglerGUI")
            settings.setValue("last_project_path", project_path)
            self.open_project(project_path)

    # ... (rest of the file as before) ...
    @Slot()
    def _on_new_file(self):
        if not self.current_project_path:
            return
        index = self.file_tree_view.currentIndex()
        dir_path = self.file_system_model.filePath(index) if index.isValid() else self.current_project_path
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)

        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(dir_path, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write("")
                self._open_file(file_path)
            else:
                QMessageBox.warning(self, "Warning", "File already exists.")

    @Slot()
    def _on_new_folder(self):
        if not self.current_project_path:
            return
        index = self.file_tree_view.currentIndex()
        dir_path = self.file_system_model.filePath(index) if index.isValid() else self.current_project_path
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)

        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            folder_path = os.path.join(dir_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            else:
                QMessageBox.warning(self, "Warning", "Folder already exists.")

    @Slot()
    def _on_refresh(self):
        if self.current_project_path:
            self._setup_file_system_model(self.current_project_path)

    @Slot()
    def _on_delete(self):
        index = self.file_tree_view.currentIndex()
        if not index.isValid():
            return

        file_path = self.file_system_model.filePath(index)
        reply = QMessageBox.question(self, 'Confirm Delete', f"Are you sure you want to delete {os.path.basename(file_path)}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if os.path.isdir(file_path):
                self.file_system_model.rmdir(index)
            else:
                self.file_system_model.remove(index)

    @Slot()
    def _on_versions_clicked(self):
        """处理版本按钮点击，显示版本历史面板并加载数据。"""
        if not self.current_project_path:
            QMessageBox.warning(self, "Warning", "Please open a project first.")
            return

        # 显示版本面板
        self.versions_dock_widget.show()
        # 加载版本数据
        self._load_versions()

    @Slot()
    def _on_deploy(self):
        if not self.current_project_path:
            QMessageBox.warning(self, "Warning", "Please open a project first.")
            return
        self.log_dock_widget.show()
        self.log_dock_widget.raise_()
        self.output_tabs.setCurrentWidget(self.log_panel)
        self.log_panel.clear()
        self.status_label.setText("Deploying...")
        self.status_animation.set_state('running')
        self.main_command_manager.execute("wrangler", ["deploy"], self.current_project_path)

    @Slot()
    def _on_dev(self):
        if not self.current_project_path:
            QMessageBox.warning(self, "Warning", "Please open a project first.")
            return
        self.is_dev_mode = True
        self.status_label.setText("Dev Running")
        self.status_animation.set_state('running')
        self.log_dock_widget.show()
        self.log_dock_widget.raise_()
        self.output_tabs.setCurrentWidget(self.log_panel)
        self.log_panel.clear()
        self.status_label.setText("Running Dev Server...")
        self.status_animation.set_state('running')
        self.main_command_manager.execute("wrangler", ["dev"], self.current_project_path)

    @Slot()
    def _on_tail_clicked(self):
        if self.is_tailing:
            self.tail_command_manager.stop()
            self.is_tailing = False
            self.tail_button.setText("Tail")
            self.tail_button.set_button_type('outline')
        else:
            if not self.current_project_path:
                QMessageBox.warning(self, "Warning", "Please open a project first.")
                return
            self.is_tailing = True
            self.log_dock_widget.show()
            self.log_dock_widget.raise_()
            self.output_tabs.setCurrentWidget(self.log_panel)
            self.log_panel.clear()
            self.log_panel.appendHtml("<span style='color:yellow;'>Starting tail...</span><br>")
            self.tail_command_manager.execute("wrangler", ["tail", "--format", "pretty"], self.current_project_path)
            self.tail_button.setText("Stop Tail")
            self.tail_button.set_button_type('primary')

    @Slot(str)
    def _on_tail_output_received(self, text):
        line = text.strip()
        if not line:
            return

        color = "#E0E0E0"  # Default color
        if "GET" in line or "POST" in line or "PUT" in line or "DELETE" in line:
            color = "#61AFEF"  # Blue
        elif "Error" in line or "Exception" in line:
            color = "#FF6B6B"  # Red
        elif " 200 " in line or " OK " in line:
            color = "#00A651"  # Green

        escaped_line = html.escape(line)
        self.log_panel.appendHtml(f"<span style='color:{color};'>{escaped_line}</span><br>")
        
        cursor = self.log_panel.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_panel.setTextCursor(cursor)

    def _load_versions(self):
        """执行 wrangler versions list --json 命令加载版本列表。"""
        if not self.current_project_path:
            return
        self.versions_table.setRowCount(0)  # 清空表格
        self.status_label.setText("Loading versions...")
        self.status_animation.set_state('running')
        self.versions_command_manager.execute("wrangler", ["versions", "list", "--json"], self.current_project_path)

    @Slot(object)
    def _on_versions_loaded(self, versions_data):
        """处理版本列表 JSON 数据。"""
        print("Versions data received:", type(versions_data), versions_data)
        if not isinstance(versions_data, list):
            # 可能不是版本数据，忽略
            print("Versions data is not a list")
            return

        self.versions_table.setRowCount(len(versions_data))
        for i, version in enumerate(versions_data):
            # Version ID（只显示前8位）
            version_id = version.get('id', '')
            short_id = version_id[:8] if version_id else ''
            id_item = QTableWidgetItem(short_id)

            # 时间（格式 MM-DD HH:mm）
            created_on = version.get('created_on', '')
            time_str = ''
            if created_on:
                # 解析 ISO 时间字符串，转换为本地时间
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(created_on.replace('Z', '+00:00'))
                    time_str = dt.strftime('%m-%d %H:%M')
                except:
                    time_str = created_on[:16]  # 备用方案
            time_item = QTableWidgetItem(time_str)

            # 状态（Active / Previous）
            is_active = version.get('active', False)
            status_item = QTableWidgetItem('Active' if is_active else 'Previous')

            # 操作按钮
            rollback_button = QPushButton("Rollback")
            rollback_button.setStyleSheet("""
                QPushButton {
                    background-color: #F6821F;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #E07010;
                }
                QPushButton:disabled {
                    background-color: #CCCCCC;
                    color: #666666;
                }
            """)
            if is_active:
                rollback_button.setEnabled(False)  # Active 行置灰
            else:
                rollback_button.clicked.connect(lambda checked, vid=version_id: self._on_rollback_version(vid))

            # 设置行样式
            if is_active:
                # Active 版本行背景 rgba(246,130,31,0.08)
                id_item.setBackground(QColor(246, 130, 31, 20))
                time_item.setBackground(QColor(246, 130, 31, 20))
                status_item.setBackground(QColor(246, 130, 31, 20))
                # ID 列前景色橙色
                id_item.setForeground(QColor("#F6821F"))

            # 添加到表格
            self.versions_table.setItem(i, 0, id_item)
            self.versions_table.setItem(i, 1, time_item)
            self.versions_table.setItem(i, 2, status_item)
            self.versions_table.setCellWidget(i, 3, rollback_button)

        self.status_animation.set_state('idle')
        self.status_label.setText(f"Loaded {len(versions_data)} versions")

    @Slot(int, QProcess.ExitStatus)
    def _on_versions_process_finished(self, exit_code, exit_status):
        """版本命令执行完成。"""
        self.status_animation.set_state('idle')
        if exit_status == QProcess.CrashExit:
            self.status_label.setText("Versions command crashed")
        else:
            # 状态已经在 _on_versions_loaded 中更新
            pass
        # 如果设置了重新加载标志（例如 rollback 完成后），重新加载版本列表
        if self.pending_versions_reload:
            self.pending_versions_reload = False
            QTimer.singleShot(500, self._load_versions)

    def _on_rollback_version(self, version_id):
        """回滚到指定版本。"""
        if not version_id:
            return

        short_id = version_id[:8]
        reply = QMessageBox.question(self, "Confirm Rollback",
                                     f"Rollback to version {short_id}?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.log_dock_widget.show()
            self.log_dock_widget.raise_()
            self.output_tabs.setCurrentWidget(self.log_panel)
            self.log_panel.clear()
            self.log_panel.appendHtml(f"<span style='color:yellow;'>Rolling back to version {short_id}...</span><br>")
            self.status_label.setText(f"Rolling back to {short_id}...")
            self.status_animation.set_state('running')
            # 设置重新加载标志
            self.pending_versions_reload = True
            # 使用 versions_command_manager 执行 rollback
            self.versions_command_manager.execute("wrangler", ["rollback", version_id], self.current_project_path)

    @Slot(QTreeWidgetItem)
    def _on_kv_namespace_expanded(self, item):
        """当 KV Namespaces 根项目展开时加载命名空间列表。"""
        if item != self.kv_namespaces_root:
            return
        # 如果已经有子项目，不再重复加载
        if item.childCount() > 0:
            return
        # 执行 wrangler kv namespace list --json
        self.kv_command_manager.execute("wrangler", ["kv", "namespace", "list", "--json"], self.current_project_path)

    @Slot(dict)
    def _on_kv_namespaces_loaded(self, data):
        """处理 KV 命名空间列表或 key 列表 JSON 数据。"""
        if not isinstance(data, list):
            return
        if self.waiting_for_kv_keys:
            # 处理 key 列表
            self.waiting_for_kv_keys = False
            self.kv_key_list.clear()
            for key_obj in data:
                key_name = key_obj.get('name', '')
                if key_name:
                    self.kv_key_list.addItem(key_name)
            self.status_label.setText(f"Loaded {len(data)} keys")
        else:
            # 处理命名空间列表
            self.kv_namespaces_root.takeChildren()  # 清空现有子项目
            for ns in data:
                ns_id = ns.get('id', '')
                title = ns.get('title', '')
                if not ns_id:
                    continue
                short_id = ns_id[:8] if ns_id else ''
                display_text = f"{title} ({short_id})"
                item = QTreeWidgetItem(self.kv_namespaces_root, [display_text])
                item.setData(0, Qt.UserRole, ns_id)  # 存储完整 ID
                item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)  # 显示可展开指示器
                # 点击命名空间时加载 key 列表
            self.kv_namespaces_root.setExpanded(True)

    @Slot(int, QProcess.ExitStatus)
    def _on_kv_process_finished(self, exit_code, exit_status):
        """KV 命令执行完成。"""
        # 可以在这里处理错误或状态更新
        pass

    @Slot(QTreeWidgetItem)
    def _on_kv_namespace_clicked(self, item):
        """点击 KV 命名空间项目时加载 key 列表。"""
        # 忽略根项目
        if item == self.kv_namespaces_root:
            return
        ns_id = item.data(0, Qt.UserRole)
        if not ns_id:
            return
        self.current_kv_namespace_id = ns_id
        # 显示 KV Browser 标签页
        self.editor_tabs.setTabVisible(self.kv_browser_tab_index, True)
        self.editor_tabs.setCurrentIndex(self.kv_browser_tab_index)
        # 加载 key 列表
        self._load_kv_keys(ns_id)

    def _load_kv_keys(self, namespace_id):
        """执行 wrangler kv key list 命令加载指定命名空间的 key 列表。"""
        self.kv_key_list.clear()
        self.kv_value_preview.clear()
        self.status_label.setText("Loading KV keys...")
        self.waiting_for_kv_keys = True
        self.kv_command_manager.execute("wrangler", ["kv", "key", "list", "--namespace-id", namespace_id, "--json"], self.current_project_path)

    @Slot(str)
    def _on_kv_search_text_changed(self, text):
        """根据搜索文本过滤 key 列表。"""
        for i in range(self.kv_key_list.count()):
            item = self.kv_key_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_kv_key_selected(self, current, previous):
        """选中 key 时加载其 value。"""
        if not current or not self.current_kv_namespace_id:
            return
        key = current.text()
        self.kv_command_manager.execute("wrangler", ["kv", "key", "get", key, "--namespace-id", self.current_kv_namespace_id], self.current_project_path)

    @Slot()
    def _on_kv_new_key(self):
        """打开 New Key 对话框。"""
        if not self.current_kv_namespace_id:
            QMessageBox.warning(self, "No Namespace", "Please select a KV namespace first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("New Key")
        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()
        key_edit = QLineEdit()
        form_layout.addRow("Key:", key_edit)
        value_edit = QPlainTextEdit()
        form_layout.addRow("Value:", value_edit)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            key = key_edit.text().strip()
            value = value_edit.toPlainText().strip()
            if not key:
                QMessageBox.warning(self, "Invalid Input", "Key cannot be empty.")
                return
            # 执行 wrangler kv key put
            self.kv_command_manager.execute("wrangler", ["kv", "key", "put", key, value, "--namespace-id", self.current_kv_namespace_id], self.current_project_path)
            # 刷新 key 列表
            self._load_kv_keys(self.current_kv_namespace_id)

    @Slot()
    def _on_kv_delete_key(self):
        """删除选中的 key。"""
        current = self.kv_key_list.currentItem()
        if not current or not self.current_kv_namespace_id:
            QMessageBox.warning(self, "No Selection", "Please select a key to delete.")
            return
        key = current.text()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Delete key '{key}'?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.kv_command_manager.execute("wrangler", ["kv", "key", "delete", key, "--namespace-id", self.current_kv_namespace_id], self.current_project_path)
            # 1秒后刷新 key 列表
            QTimer.singleShot(1000, lambda: self._load_kv_keys(self.current_kv_namespace_id))

    @Slot()
    def _on_kv_refresh(self):
        """重新加载当前命名空间的 key 列表。"""
        if self.current_kv_namespace_id:
            self._load_kv_keys(self.current_kv_namespace_id)

    @Slot(str)
    def _on_kv_output_received(self, text):
        """处理 KV 命令的原始输出（例如 key get 的结果）。"""
        # 尝试解析为 JSON 并美化输出
        try:
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2)
            self.kv_value_preview.setPlainText(formatted)
        except json.JSONDecodeError:
            # 不是 JSON，直接显示原文
            self.kv_value_preview.setPlainText(text)

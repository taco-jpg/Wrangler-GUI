import os
import re
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QLabel, QFileDialog, QTreeView, QPlainTextEdit, 
    QToolBar, QProgressBar, QDockWidget, QStatusBar, QSystemTrayIcon, 
    QGraphicsDropShadowEffect, QStackedWidget, QFileSystemModel, 
    QInputDialog, QMessageBox, QStyle, QApplication, QTabWidget
)
from PySide6.QtGui import (
    QFont, QAction, QIcon, QColor, QKeySequence, QDesktopServices, QShortcut, QTextCursor
)
from PySide6.QtCore import Qt, Slot, QProcess, QPropertyAnimation, QEasingCurve, QSize, QPoint, QUrl

from .theme import COLORS, get_font
from .code_editor import CodeEditor
from .settings_panel import SettingsPanel
from .icon_provider import FileIconProvider
from .animated_button import AnimatedButton
from .breathing_dot import BreathingDot
from .terminal import Terminal
from .animations import apply_pulse_animation
from core.processor import CommandManager

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wrangler-Desktop")
        self.setGeometry(100, 100, 1200, 800)
        self.command_manager = CommandManager(self)
        self.current_project_path = None
        self.open_files = {}
        self.is_dev_mode = False
        self._setup_ui()
        self._setup_styles()
        self._setup_signals()

    def _setup_ui(self):
        editor_widget = self._create_editor_widget()
        self.setCentralWidget(editor_widget)
        self._setup_toolbar()
        self._setup_tray_icon()
        self._setup_log_dock()
        self._setup_status_bar()

    def _create_editor_widget(self):
        main_splitter = QSplitter(Qt.Horizontal, self)
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([260, 940])
        return main_splitter

    def _create_left_panel(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_widget.setStyleSheet(f"background-color: {COLORS['BACKGROUND_SECONDARY'].name()}; border-right: 1px solid {COLORS['BORDER_DEFAULT'].name()};")
        file_toolbar = self._create_file_toolbar()
        self.file_tree_view = QTreeView()
        self.file_tree_view.setHeaderHidden(True)
        self.file_tree_view.setAnimated(True)
        left_layout.addWidget(file_toolbar)
        left_layout.addWidget(self.file_tree_view)
        return left_widget

    def _create_file_toolbar(self):
        file_toolbar = QToolBar("File Toolbar")
        file_toolbar.setFixedHeight(40)
        new_file_button = AnimatedButton("New File", button_type='secondary')
        new_file_button.clicked.connect(self._on_new_file)
        file_toolbar.addWidget(new_file_button)
        return file_toolbar

    def _create_right_panel(self):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.settings_panel = SettingsPanel(command_manager=self.command_manager)
        self.editor_tabs.addTab(self.settings_panel, "Settings")
        return self.editor_tabs

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setFixedHeight(48)
        self.addToolBar(toolbar)
        self.open_project_button = AnimatedButton("Open Project", button_type='secondary')
        self.open_project_button.clicked.connect(self._on_open_project)
        toolbar.addWidget(self.open_project_button)
        toolbar.addSeparator()
        self.deploy_button = AnimatedButton("Deploy", button_type='primary')
        self.deploy_button.clicked.connect(self._on_deploy)
        toolbar.addWidget(self.deploy_button)
        self.dev_button = AnimatedButton("Dev", button_type='outline')
        self.dev_button.clicked.connect(self._on_dev)
        toolbar.addWidget(self.dev_button)
        self.stop_button = AnimatedButton("Stop", button_type='outline')
        self.stop_button.clicked.connect(self.command_manager.stop)
        toolbar.addWidget(self.stop_button)
        self.deploy_button.hide()
        self.dev_button.hide()
        self.stop_button.hide()

    def _setup_log_dock(self):
        self.log_dock_widget = QDockWidget("Output", self)
        self.log_dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.output_tabs = QTabWidget()
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setFont(get_font("CODE"))
        self.terminal = Terminal()
        self.output_tabs.addTab(self.log_panel, "Logs")
        self.output_tabs.addTab(self.terminal, "Terminal")
        self.log_dock_widget.setWidget(self.output_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock_widget)
        self.log_dock_widget.setVisible(False)

    def _setup_status_bar(self):
        self.setStatusBar(QStatusBar(self))
        self.statusBar().setFixedHeight(28)
        self.status_label = QLabel("Ready")
        self.status_animation = BreathingDot(self)
        self.statusBar().addPermanentWidget(self.status_animation)
        self.statusBar().addPermanentWidget(self.status_label)
        self.status_animation.set_state('idle')

    def _setup_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {COLORS["BACKGROUND_PRIMARY"].name()}; color: {COLORS["TEXT_PRIMARY"].name()}; }}
            QToolBar {{ background-color: {COLORS["BACKGROUND_PRIMARY"].name()}; border-bottom: 1px solid {COLORS["BORDER_DEFAULT"].name()}; spacing: 8px; padding: 0 12px; }}
            QSplitter::handle {{ background-color: {COLORS["BORDER_DEFAULT"].name()}; }}
            QSplitter::handle:horizontal {{ width: 1px; }}
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{ background: transparent; color: {COLORS["TEXT_SECONDARY"].name()}; font-size: 14px; padding: 0 16px; border: none; height: 44px; }}
            QTabBar::tab:selected {{ color: {COLORS["TEXT_PRIMARY"].name()}; border-bottom: 3px solid {COLORS["ACCENT_ORANGE"].name()}; }}
            QTabBar::tab:hover:!selected {{ color: {COLORS["TEXT_PRIMARY"].name()}; }}
            QTabBar::close-button {{ image: url(none); }}
            QTreeView {{ border: none; padding: 8px; background-color: transparent; }}
            QTreeView::item {{ height: 32px; border-radius: 4px; }}
            QTreeView::item:hover {{ background-color: {COLORS["BACKGROUND_TERTIARY"].name()}; }}
            QTreeView::item:selected {{ background-color: {COLORS["ACCENT_ORANGE_LIGHT"].name()}; color: {COLORS["ACCENT_ORANGE"].name()}; border-left: 3px solid {COLORS["ACCENT_ORANGE"].name()}; }}
            QStatusBar {{ background-color: {COLORS["BACKGROUND_SECONDARY"].name()}; border-top: 1px solid {COLORS["BORDER_DEFAULT"].name()}; }}
            QStatusBar QLabel {{ color: {COLORS["TEXT_SECONDARY"].name()}; padding: 0 8px; }}
            QDockWidget {{ border-top: 1px solid {COLORS["BORDER_DEFAULT"].name()}; }}
            #LogPanel {{ background-color: {COLORS["CODE_BG"].name()}; color: #E0E0E0; }}
        """)
        self.editor_tabs.setFont(get_font("UI_BOLD"))
        self.log_panel.setObjectName("LogPanel")

    def _setup_signals(self):
        self.editor_tabs.tabCloseRequested.connect(self._on_close_tab)
        self.editor_tabs.currentChanged.connect(self._on_main_tab_changed)
        self.command_manager.output_received.connect(self._on_output_received)
        self.command_manager.process_finished.connect(self._on_process_finished)
        self.file_tree_view.doubleClicked.connect(self._on_file_tree_double_clicked)
        self.settings_panel.login_requested.connect(self._on_login)
        self.settings_panel.logout_requested.connect(self._on_logout)
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence.StandardKey.Save, self, self._on_save_file)
        QShortcut(QKeySequence("Cmd+Shift+S"), self, self._on_save_all_files)
        QShortcut(QKeySequence.StandardKey.Open, self, self._on_open_project)
        QShortcut(QKeySequence.StandardKey.New, self, self._on_new_file)
        QShortcut(QKeySequence.StandardKey.Close, self, lambda: self._on_close_tab(self.editor_tabs.currentIndex()))
        QShortcut(QKeySequence("Cmd+R"), self, self._on_dev)
        QShortcut(QKeySequence("Cmd+Shift+D"), self, self._on_deploy)
        QShortcut(QKeySequence("Ctrl+`"), self, self.log_dock_widget.toggleViewAction().trigger)
        QShortcut(QKeySequence("Cmd+B"), self, lambda: self.main_splitter.widget(0).setVisible(not self.main_splitter.widget(0).isVisible()))
        QShortcut(QKeySequence("Cmd+,"), self, lambda: self.editor_tabs.setCurrentWidget(self.settings_panel))

    @Slot()
    def _on_save_file(self):
        current_widget = self.editor_tabs.currentWidget()
        if isinstance(current_widget, CodeEditor):
            current_widget.save_file()

    @Slot()
    def _on_save_all_files(self):
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, CodeEditor):
                widget.save_file()

    @Slot()
    def _on_open_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory", os.path.expanduser("~"))
        if project_path:
            self.current_project_path = project_path
            self._setup_file_system_model(project_path)
            self.settings_panel.set_project(project_path)
            self.deploy_button.show()
            self.dev_button.show()
            self.stop_button.show()

    @Slot(int)
    def _on_close_tab(self, index):
        if self.editor_tabs.widget(index) == self.settings_panel: return
        widget = self.editor_tabs.widget(index)
        if widget and widget.property("file_path") in self.open_files:
            del self.open_files[widget.property("file_path")]
        self.editor_tabs.removeTab(index)
        widget.deleteLater()

    @Slot('QModelIndex')
    def _on_file_tree_double_clicked(self, index):
        file_path = self.fs_model.filePath(index)
        if not self.fs_model.isDir(index):
            if file_path in self.open_files:
                self.editor_tabs.setCurrentWidget(self.open_files[file_path])
            else:
                editor = CodeEditor()
                editor.setProperty("file_path", file_path)
                editor.open_file(file_path)
                editor.modificationChanged.connect(lambda modified, p=file_path: self._on_modification_changed(p, modified))
                index = self.editor_tabs.addTab(editor, os.path.basename(file_path))
                self.editor_tabs.setCurrentIndex(index)
                self.open_files[file_path] = editor

    @Slot(str, bool)
    def _on_modification_changed(self, file_path, modified):
        if file_path in self.open_files:
            widget = self.open_files[file_path]
            index = self.editor_tabs.indexOf(widget)
            if index != -1:
                title = os.path.basename(file_path)
                if modified:
                    self.editor_tabs.setTabText(index, title + " •")
                else:
                    self.editor_tabs.setTabText(index, title)

    @Slot()
    def _on_deploy(self):
        if not self.current_project_path: return
        self.log_panel.clear()
        self.log_panel.appendPlainText("Starting deployment...")
        self.deploy_button.setEnabled(False)
        self.dev_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_dock_widget.show()
        self.status_label.setText("Deploying...")
        self.status_animation.set_state('running')
        self.pulse_animation = apply_pulse_animation(self.deploy_button)
        self.pulse_animation.start()
        self.command_manager.execute("wrangler", ["deploy"], self.current_project_path)

    @Slot()
    def _on_dev(self):
        if self.is_dev_mode:
            self.command_manager.stop()
            return

        if not self.current_project_path: return
        self.log_panel.clear()
        self.log_panel.appendPlainText("Starting dev server...")
        self.deploy_button.setEnabled(False)
        self.dev_button.setText("Stop Dev")
        self.is_dev_mode = True
        self.log_dock_widget.show()
        self.status_label.setText("Running Dev Server...")
        self.status_animation.set_state('running')
        self.command_manager.execute("wrangler", ["dev"], self.current_project_path)

    @Slot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code, exit_status):
        self.status_animation.set_state('success' if exit_status == QProcess.NormalExit and exit_code == 0 else 'error')
        if hasattr(self, 'pulse_animation'):
            self.pulse_animation.stop()
            self.deploy_button.setWindowOpacity(1.0)
        
        if self.is_dev_mode:
            self.dev_button.setText("Dev")
            self.is_dev_mode = False

        self.deploy_button.setEnabled(True)
        self.dev_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    @Slot(int)
    def _on_main_tab_changed(self, index):
        widget = self.editor_tabs.widget(index)
        if widget == self.settings_panel:
            self.settings_panel.load_secrets()

    @Slot(str)
    def _on_output_received(self, text):
        url_pattern = re.compile(r'https?://[\w\-.:]+')
        match = url_pattern.search(text)
        if match:
            url = match.group(0)
            text = text.replace(url, f'<a href="{url}">{url}</a>')
            self.log_panel.document().setHtml(self.log_panel.toPlainText() + text)
            self.log_panel.moveCursor(QTextCursor.End)
        else:
            self.log_panel.appendPlainText(text)

    def _setup_file_system_model(self, project_path):
        self.fs_model = QFileSystemModel()
        self.fs_model.setIconProvider(FileIconProvider())
        self.fs_model.setRootPath(project_path)
        self.file_tree_view.setModel(self.fs_model)
        self.file_tree_view.setRootIndex(self.fs_model.index(project_path))
        for i in range(1, self.fs_model.columnCount()):
            self.file_tree_view.hideColumn(i)

    def _setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setVisible(True)

    @Slot()
    def _on_new_file(self):
        pass # Implement later

    @Slot()
    def _on_login(self):
        self.command_manager.execute("wrangler", ["login"])

    @Slot()
    def _on_logout(self):
        self.command_manager.execute("wrangler", ["logout"])

    def closeEvent(self, event):
        self.command_manager.stop()
        super().closeEvent(event)

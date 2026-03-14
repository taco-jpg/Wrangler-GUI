import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings
from ui.main_window import MainWindow
from ui.welcome_screen import WelcomeScreen
from ui.theme import initialize_fonts, get_font

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        initialize_fonts()
        self.app.setFont(get_font("UI"))
        self.main_window = None
        self.welcome_screen = None

    def run(self):
        settings = QSettings("WranglerGUI", "WranglerGUI")
        last_project_path = settings.value("last_project_path")

        if last_project_path and os.path.isdir(last_project_path):
            self.show_main_window(project_path=last_project_path)
        else:
            self.welcome_screen = WelcomeScreen()
            self.welcome_screen.open_project_requested.connect(self.show_main_window)
            self.welcome_screen.show()
        
        sys.exit(self.app.exec())

    def show_main_window(self, project_path=None):
        if self.welcome_screen:
            self.welcome_screen.close()
        
        if not self.main_window:
            self.main_window = MainWindow()
        
        self.main_window.show()

        if project_path:
            self.main_window.open_project(project_path)
        else:
            self.main_window._on_open_project()

def main():
    from shutil import which
    if not which("wrangler"):
        QMessageBox.critical(None, "Error", "'wrangler' command not found.\nPlease install it using: npm install -g wrangler")
        sys.exit(1)

    controller = AppController()
    controller.run()

if __name__ == "__main__":
    main()

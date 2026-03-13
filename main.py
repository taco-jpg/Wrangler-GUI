import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.welcome_screen import WelcomeScreen
from ui.theme import get_font

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setFont(get_font("UI"))
        
        self.main_window = None
        self.welcome_screen = WelcomeScreen()
        self.welcome_screen.open_project_requested.connect(self.show_main_window)

    def run(self):
        self.welcome_screen.show()
        sys.exit(self.app.exec())

    def show_main_window(self):
        self.welcome_screen.close()
        if not self.main_window:
            self.main_window = MainWindow()
        self.main_window.show()
        self.main_window._on_open_project() # Trigger file dialog immediately

def main():
    # Check for wrangler installation first
    from shutil import which
    if not which("wrangler"):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", "'wrangler' command not found.\nPlease install it using: npm install -g wrangler")
        sys.exit(1)

    controller = AppController()
    controller.run()

if __name__ == "__main__":
    main()


import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def load_stylesheet(app):
    """加载QSS样式表。"""
    # 获取 main.py 文件的绝对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建样式表文件的路径
    stylesheet_path = os.path.join(base_dir, 'assets', 'style.qss')
    
    if not os.path.exists(stylesheet_path):
        print(f"Warning: Stylesheet not found at {stylesheet_path}")
        return

    with open(stylesheet_path, "r") as f:
        style = f.read()
        app.setStyleSheet(style)

def main():
    """应用主入口函数。"""
    app = QApplication(sys.argv)
    
    # 加载样式
    load_stylesheet(app)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 启动事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    # 检查 wrangler 是否安装
    from shutil import which
    if not which("wrangler"):
        print("Error: 'wrangler' command not found.")
        print("Please install it using: npm install -g wrangler")
        sys.exit(1)
        
    main()


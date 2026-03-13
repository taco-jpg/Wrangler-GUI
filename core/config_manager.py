
import toml
import os

class ConfigManager:
    """负责读取、解析和写入 wrangler.toml 文件。"""

    def __init__(self, project_path=None):
        self.project_path = project_path
        self.config_path = None
        self.data = {}
        if project_path:
            self.set_project_path(project_path)

    def set_project_path(self, project_path):
        """设置项目路径并尝试加载配置文件。"""
        self.project_path = project_path
        self.config_path = os.path.join(project_path, 'wrangler.toml')
        self.load()

    def load(self):
        """从 wrangler.toml 文件加载配置。"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.data = toml.load(f)
                return True
            except Exception as e:
                print(f"Error loading config file: {e}")
                self.data = {}
                return False
        return False

    def save(self):
        """将当前配置数据保存回 wrangler.toml 文件。"""
        if self.config_path:
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    toml.dump(self.data, f)
                return True
            except Exception as e:
                print(f"Error saving config file: {e}")
                return False
        return False

    def get(self, key, default=None):
        """获取一个配置项。"""
        return self.data.get(key, default)

    def set(self, key, value):
        """设置一个配置项。"""
        self.data[key] = value

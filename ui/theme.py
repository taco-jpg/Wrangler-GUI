from PySide6.QtGui import QColor, QFont, QFontDatabase

# --- Color Palette ---
COLORS = {
    "BACKGROUND_PRIMARY": QColor("#FFFFFF"),
    "BACKGROUND_SECONDARY": QColor("#F6F6F6"),
    "BACKGROUND_TERTIARY": QColor("#EFEFEF"),
    "BORDER_DEFAULT": QColor("#E2E2E2"),
    "BORDER_STRONG": QColor("#AAAAAA"),
    "TEXT_PRIMARY": QColor("#1A1A1A"),
    "TEXT_SECONDARY": QColor("#5C5C5C"),
    "TEXT_MUTED": QColor("#999999"),
    "ACCENT_ORANGE": QColor("#F6821F"),
    "ACCENT_ORANGE_HOVER": QColor("#E07010"),
    "ACCENT_ORANGE_PRESS": QColor("#C85E00"),
    "ACCENT_ORANGE_LIGHT": QColor("#FFF3E8"),
    "SUCCESS": QColor("#00A651"),
    "ERROR": QColor("#E53E3E"),
    "CODE_BG": QColor("#1E1E1E"),
}

SYSTEM_FONT = ""
FONTS = {}

def initialize_fonts():
    global SYSTEM_FONT, FONTS

    def get_system_font_family() -> str:
        preferred = ["SF Pro Display", "SF Pro Text", "Helvetica Neue", "Arial"]
        available = QFontDatabase.families()
        for f in preferred:
            if f in available:
                return f
        return ""

    SYSTEM_FONT = get_system_font_family()

    FONTS = {
        "UI": QFont(SYSTEM_FONT, 13),
        "UI_BOLD": QFont(SYSTEM_FONT, 13, QFont.Weight.Bold),
        "CODE": QFont("'SF Mono', 'Fira Code', 'Cascadia Code', monospace", 13),
        "SECTION_TITLE": QFont(SYSTEM_FONT, 12, QFont.Weight.Bold),
    }

def get_font(name="UI"):
    """Helper to get a font from the font dictionary."""
    if not FONTS:  # 如果字体未初始化，先初始化
        initialize_fonts()
    return FONTS.get(name, FONTS["UI"])

def get_color(name):
    """Helper to get a color from the color dictionary."""
    return COLORS.get(name, QColor("#000000"))

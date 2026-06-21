import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "notes.json")

MIN_WIDTH = 150
MIN_HEIGHT = 120
DEFAULT_WIDTH = 220
DEFAULT_HEIGHT = 220
HEADER_HEIGHT = 28

DEBOUNCE_SAVE_DELAY = 500
AUTO_SAVE_INTERVAL = 30000

TEXT_FG = "#212121"
PIN_FG = "#C62828"
PANEL_BG = "#FAFAFA"
HINT_FG = "#9E9E9E"
BORDER_DEFAULT = "#BDBDBD"

FONT_FAMILY = "Microsoft YaHei"
FONT_SIZE = 10
HEADER_FONT_SIZE = 9
TITLE_FONT_SIZE = 12
TAG_FONT_SIZE = 8

COLORS = {
    "yellow": {"name": "黄", "bg": "#FFF9C4", "header": "#FDD835", "border": "#F9A825"},
    "pink":   {"name": "粉", "bg": "#FCE4EC", "header": "#F48FB1", "border": "#AD1457"},
    "blue":   {"name": "蓝", "bg": "#E3F2FD", "header": "#64B5F6", "border": "#1565C0"},
    "green":  {"name": "绿", "bg": "#E8F5E9", "header": "#81C784", "border": "#2E7D32"},
    "white":  {"name": "白", "bg": "#FFFFFF", "header": "#E0E0E0", "border": "#616161"},
}
DEFAULT_COLOR = "yellow"

HOTKEY_NEW_NOTE = "ctrl+shift+n"

PANEL_TITLE = "桌面便签"
PANEL_GEOMETRY = "260x200+50+50"
NEW_NOTE_ACTIVE_BG = "#FBC02D"
SHOW_ALL_BTN_BG = "#ECEFF1"
SHOW_ALL_BTN_ACTIVE_BG = "#CFD8DC"

HINT_TEXT = "Ctrl+Shift+N 新建 · Ctrl+S 保存 · Ctrl+B 加粗"
HINT_NO_KEYBOARD = "提示：未安装 keyboard 库，全局快捷键不可用"

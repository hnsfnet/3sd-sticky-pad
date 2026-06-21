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

_DEFAULTS = {
    "data_file": DATA_FILE,
    "min_width": MIN_WIDTH,
    "min_height": MIN_HEIGHT,
    "default_width": DEFAULT_WIDTH,
    "default_height": DEFAULT_HEIGHT,
    "header_height": HEADER_HEIGHT,
    "debounce_save_delay": DEBOUNCE_SAVE_DELAY,
    "auto_save_interval": AUTO_SAVE_INTERVAL,
    "text_fg": TEXT_FG,
    "pin_fg": PIN_FG,
    "panel_bg": PANEL_BG,
    "hint_fg": HINT_FG,
    "border_default": BORDER_DEFAULT,
    "font_family": FONT_FAMILY,
    "font_size": FONT_SIZE,
    "header_font_size": HEADER_FONT_SIZE,
    "title_font_size": TITLE_FONT_SIZE,
    "tag_font_size": TAG_FONT_SIZE,
    "colors": dict(COLORS),
    "default_color": DEFAULT_COLOR,
    "hotkey_new_note": HOTKEY_NEW_NOTE,
    "panel_title": PANEL_TITLE,
    "panel_geometry": PANEL_GEOMETRY,
    "new_note_active_bg": NEW_NOTE_ACTIVE_BG,
    "show_all_btn_bg": SHOW_ALL_BTN_BG,
    "show_all_btn_active_bg": SHOW_ALL_BTN_ACTIVE_BG,
    "hint_text": HINT_TEXT,
    "hint_no_keyboard": HINT_NO_KEYBOARD,
}


class AppConfig:
    def __init__(self, overrides=None):
        self._values = dict(_DEFAULTS)
        if overrides:
            self.update(overrides)

    def get(self, key, default=None):
        return self._values.get(key, default)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._values:
            return self._values[name]
        raise AttributeError(f"'AppConfig' object has no attribute '{name}'")

    def __getitem__(self, key):
        if key not in self._values:
            raise KeyError(key)
        return self._values[key]

    def __setitem__(self, key, value):
        self._values[key] = value

    def set(self, key, value):
        self._values[key] = value

    def update(self, overrides):
        for k, v in overrides.items():
            if k in self._values:
                self._values[k] = v

    def items(self):
        return self._values.items()

    def keys(self):
        return self._values.keys()

    def to_dict(self):
        return dict(self._values)

    def reset(self):
        self._values = dict(_DEFAULTS)

    def has(self, key):
        return key in self._values

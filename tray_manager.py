import threading

import pystray
from PIL import Image, ImageDraw

import config


class TrayManager:
    def __init__(self, root, note_manager, on_new_note, on_show_all, on_quit):
        self.root = root
        self.note_manager = note_manager
        self._on_new_note = on_new_note
        self._on_show_all = on_show_all
        self._on_quit = on_quit
        self._icon = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _create_image(self):
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        c = config.COLORS["yellow"]
        draw.rectangle([4, 6, size - 6, size - 4], fill=c["bg"], outline=c["border"], width=2)
        draw.rectangle([4, 6, size - 6, 18], fill=c["header"])
        for y in [26, 36, 46]:
            draw.line([(10, y), (size - 12, y)], fill="#BDBDBD", width=2)
        return img

    def _build_menu(self):
        items = [
            pystray.MenuItem("新建便签", self._new_note_cb, default=True),
            pystray.MenuItem("显示所有便签", self._show_all_cb),
        ]
        tags = self.note_manager.get_tags()
        if self.note_manager.has_notes():
            sub_items = [
                pystray.MenuItem("全部便签", self._show_all_cb),
                pystray.MenuItem("无标签",
                                 lambda icon, item: self.root.after(0, lambda: self.note_manager.filter_by_tag(None))),
            ]
            if tags:
                sub_items.append(pystray.Menu.SEPARATOR)
                for t in tags:
                    sub_items.append(
                        pystray.MenuItem(
                            t,
                            lambda icon, item, t=t: self.root.after(0, lambda: self.note_manager.filter_by_tag(t))
                        )
                    )
            items.append(pystray.MenuItem("按标签筛选", None, submenu=pystray.Menu(*sub_items)))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("退出", self._quit_cb))
        return pystray.Menu(*items)

    def _run(self):
        self._icon = pystray.Icon(
            "sticky_notes", self._create_image(), config.PANEL_TITLE, self._build_menu
        )
        self._icon.run()

    def _new_note_cb(self, icon=None, item=None):
        self.root.after(0, self._on_new_note)

    def _show_all_cb(self, icon=None, item=None):
        self.root.after(0, self._on_show_all)

    def _quit_cb(self, icon=None, item=None):
        if self._icon:
            self._icon.stop()
        self.root.after(0, self._on_quit)

    def refresh_menu(self):
        if self._icon is not None:
            try:
                self._icon.update_menu()
            except Exception:
                pass

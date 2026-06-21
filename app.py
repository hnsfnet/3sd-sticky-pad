import tkinter as tk

import config
from note_manager import NoteManager
from tray_manager import TrayManager
from hotkey_manager import HotkeyManager, HAS_KEYBOARD


class ControlPanel:
    def __init__(self, root, note_manager, on_close):
        self.root = root
        self.note_manager = note_manager
        self._on_close = on_close

        self.root.title(config.PANEL_TITLE)
        self.root.geometry(config.PANEL_GEOMETRY)
        self.root.resizable(False, False)
        self.root.configure(bg=config.PANEL_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        frame = tk.Frame(self.root, bg=config.PANEL_BG)
        frame.pack(expand=True, fill="both", padx=20, pady=12)

        tk.Label(
            frame, text=config.PANEL_TITLE, bg=config.PANEL_BG, fg=config.TEXT_FG,
            font=(config.FONT_FAMILY, config.TITLE_FONT_SIZE, "bold")
        ).pack(pady=(0, 6))

        color_frame = tk.Frame(frame, bg=config.PANEL_BG)
        color_frame.pack(fill="x", pady=(0, 8))
        tk.Label(color_frame, text="颜色：", bg=config.PANEL_BG, fg=config.TEXT_FG,
                font=(config.FONT_FAMILY, config.HEADER_FONT_SIZE)).pack(side="left")
        self.color_buttons = {}
        for key in config.COLORS:
            btn = tk.Button(
                color_frame, width=2, height=1, relief="flat", bd=1,
                bg=config.COLORS[key]["bg"], activebackground=config.COLORS[key]["bg"],
                highlightthickness=2, highlightbackground=config.BORDER_DEFAULT,
                command=lambda k=key: self._select_color(k)
            )
            btn.pack(side="left", padx=3)
            self.color_buttons[key] = btn
        self._select_color(config.DEFAULT_COLOR)

        btn_frame = tk.Frame(frame, bg=config.PANEL_BG)
        btn_frame.pack(fill="x")
        tk.Button(
            btn_frame, text="新建便签", command=self.note_manager.create_note,
            bg=config.COLORS[config.DEFAULT_COLOR]["header"], fg=config.TEXT_FG, bd=0,
            padx=16, pady=6, font=(config.FONT_FAMILY, config.HEADER_FONT_SIZE, "bold"),
            cursor="hand2", activebackground=config.NEW_NOTE_ACTIVE_BG
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Button(
            btn_frame, text="显示全部", command=self.note_manager.show_all,
            bg=config.SHOW_ALL_BTN_BG, fg=config.TEXT_FG, bd=0, padx=16, pady=6,
            font=(config.FONT_FAMILY, config.HEADER_FONT_SIZE), cursor="hand2",
            activebackground=config.SHOW_ALL_BTN_ACTIVE_BG
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        hint = config.HINT_TEXT if HAS_KEYBOARD else config.HINT_NO_KEYBOARD
        tk.Label(
            frame, text=hint, bg=config.PANEL_BG, fg=config.HINT_FG,
            font=(config.FONT_FAMILY, config.TAG_FONT_SIZE), wraplength=220, justify="left"
        ).pack(side="bottom", pady=(8, 0))

    def _select_color(self, key):
        self.note_manager.current_color = key
        for k, btn in self.color_buttons.items():
            btn.config(highlightbackground=config.PIN_FG if k == key else config.BORDER_DEFAULT,
                       relief="sunken" if k == key else "flat")


class NoteApp:
    def __init__(self):
        self.root = tk.Tk()

        self.note_manager = NoteManager(self.root)
        self.tray = TrayManager(
            self.root, self.note_manager,
            on_new_note=self.note_manager.create_note,
            on_show_all=self.restore_from_tray,
            on_quit=self.quit_app,
        )
        self.note_manager.on_saved = self.tray.refresh_menu
        self.hotkey = HotkeyManager(self.root, on_new_note=self.note_manager.create_note)

        self.control = ControlPanel(self.root, self.note_manager, on_close=self.minimize_to_tray)

        self.note_manager.load()
        self.root.after(300, self.tray.start)
        self.note_manager.start_auto_save()
        self.hotkey.register()

    def minimize_to_tray(self):
        self.note_manager.hide_all()
        self.root.withdraw()

    def restore_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.note_manager.show_all()

    def quit_app(self):
        self.note_manager.shutdown()
        self.hotkey.unregister()
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    NoteApp().run()

import tkinter as tk
from tkinter import scrolledtext
import json
import os
import uuid
import threading
import pystray
from PIL import Image, ImageDraw

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")
MIN_WIDTH = 150
MIN_HEIGHT = 120
DEFAULT_WIDTH = 220
DEFAULT_HEIGHT = 200
NOTE_BG = "#FFF9C4"
NOTE_HEADER = "#FDD835"
TEXT_FG = "#212121"
BTN_BG = "#E53935"
BTN_FG = "#FFFFFF"
RESIZE_HANDLE = 16


class StickyNote:
    def __init__(self, app, note_id=None, x=None, y=None, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, content=""):
        self.app = app
        self.note_id = note_id or str(uuid.uuid4())
        self.content = content
        self.width = max(width, MIN_WIDTH)
        self.height = max(height, MIN_HEIGHT)

        self.root = tk.Toplevel(app.root)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=NOTE_BG)
        self.root.resizable(False, False)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if x is None:
            x = (sw - self.width) // 3
        if y is None:
            y = (sh - self.height) // 3
        x = max(0, min(x, sw - self.width))
        y = max(0, min(y, sh - self.height))
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        self.header = tk.Frame(self.root, bg=NOTE_HEADER, height=26)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header, text="便签", bg=NOTE_HEADER, fg=TEXT_FG,
            font=("Microsoft YaHei", 9, "bold")
        )
        self.title_label.pack(side="left", padx=8)

        self.close_btn = tk.Label(
            self.header, text="×", bg=NOTE_HEADER, fg=BTN_BG,
            font=("Arial", 14, "bold"), cursor="hand2", padx=6
        )
        self.close_btn.pack(side="right")

        self.text = scrolledtext.ScrolledText(
            self.root, bg=NOTE_BG, fg=TEXT_FG, bd=0,
            font=("Microsoft YaHei", 10), wrap="word",
            highlightthickness=1, highlightbackground="#F9A825",
            highlightcolor="#F57F17", insertbackground=TEXT_FG
        )
        self.text.pack(fill="both", expand=True, padx=2, pady=2)
        self.text.insert("1.0", self.content)

        self.resize_handle = tk.Label(
            self.root, text="⇲", bg=NOTE_BG, fg="#9E9E9E",
            font=("Arial", 10), cursor="size_nw_se"
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)

    def _bind_events(self):
        for w in (self.header, self.title_label):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

        self.close_btn.bind("<Button-1>", lambda e: self.destroy())

        self.resize_handle.bind("<Button-1>", self._start_resize)
        self.resize_handle.bind("<B1-Motion>", self._on_resize)

        self.text.bind("<KeyRelease>", lambda e: self.app.schedule_save())
        self.root.bind("<Configure>", lambda e: self.app.schedule_save())

    def _start_drag(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _start_resize(self, event):
        self._resize_x = event.x_root
        self._resize_y = event.y_root
        self._resize_w = self.root.winfo_width()
        self._resize_h = self.root.winfo_height()

    def _on_resize(self, event):
        dw = event.x_root - self._resize_x
        dh = event.y_root - self._resize_y
        new_w = max(MIN_WIDTH, self._resize_w + dw)
        new_h = max(MIN_HEIGHT, self._resize_h + dh)
        self.root.geometry(f"{new_w}x{new_h}")

    def destroy(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.app.remove_note(self.note_id)

    def show(self):
        try:
            self.root.deiconify()
            self.root.lift()
        except tk.TclError:
            pass

    def hide(self):
        try:
            self.root.withdraw()
        except tk.TclError:
            pass

    def to_dict(self):
        try:
            g = self.root.geometry()
            size, pos = g.split("+", 1)
            w, h = map(int, size.split("x"))
            x, y = map(int, pos.split("+"))
        except Exception:
            w, h, x, y = self.width, self.height, 100, 100
        try:
            content = self.text.get("1.0", "end-1c")
        except tk.TclError:
            content = self.content
        return {
            "id": self.note_id,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "content": content
        }


class ControlPanel:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.root.title("桌面便签")
        self.root.geometry("260x110+50+50")
        self.root.resizable(False, False)
        self.root.configure(bg="#FAFAFA")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        frame = tk.Frame(self.root, bg="#FAFAFA")
        frame.pack(expand=True, fill="both", padx=20, pady=15)

        tk.Label(
            frame, text="桌面便签", bg="#FAFAFA", fg=TEXT_FG,
            font=("Microsoft YaHei", 12, "bold")
        ).pack(pady=(0, 8))

        btn_frame = tk.Frame(frame, bg="#FAFAFA")
        btn_frame.pack(fill="x")

        new_btn = tk.Button(
            btn_frame, text="新建便签", command=self.app.create_note,
            bg=NOTE_HEADER, fg=TEXT_FG, bd=0, padx=16, pady=6,
            font=("Microsoft YaHei", 9, "bold"), cursor="hand2",
            activebackground="#FBC02D"
        )
        new_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        show_btn = tk.Button(
            btn_frame, text="显示全部", command=self.app.show_all_notes,
            bg="#ECEFF1", fg=TEXT_FG, bd=0, padx=16, pady=6,
            font=("Microsoft YaHei", 9), cursor="hand2",
            activebackground="#CFD8DC"
        )
        show_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _on_close(self):
        self.app.minimize_to_tray()


class NoteApp:
    def __init__(self):
        self.root = tk.Tk()
        self.notes = {}
        self._save_timer = None
        self._tray_icon = None
        self._tray_thread = None

        self.control = ControlPanel(self)
        self.load_notes()
        self.root.after(300, self._start_tray)

    def _start_tray(self):
        self._tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self._tray_thread.start()

    def _create_icon_image(self):
        size = 64
        img = Image.new("RGB", (size, size), NOTE_BG)
        draw = ImageDraw.Draw(img)
        draw.rectangle([2, 2, size - 3, size - 3], fill=NOTE_BG, outline="#F9A825", width=2)
        draw.rectangle([2, 2, size - 3, 14], fill=NOTE_HEADER)
        for i, y in enumerate([22, 32, 42, 52]):
            w = 40 - i * 6
            draw.line([(12, y), (12 + w, y)], fill="#BDBDBD", width=2)
        return img

    def _run_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("新建便签", self._tray_new_note, default=True),
            pystray.MenuItem("显示所有便签", self._tray_show_all),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._tray_quit)
        )
        self._tray_icon = pystray.Icon(
            "sticky_notes", self._create_icon_image(), "桌面便签", menu
        )
        self._tray_icon.run()

    def _tray_new_note(self, icon=None, item=None):
        self.root.after(0, self.create_note)

    def _tray_show_all(self, icon=None, item=None):
        self.root.after(0, self._restore_from_tray)

    def _tray_quit(self, icon=None, item=None):
        if self._tray_icon:
            self._tray_icon.stop()
        self.root.after(0, self.quit_app)

    def _restore_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.show_all_notes()

    def minimize_to_tray(self):
        self.hide_all_notes()
        self.root.withdraw()

    def create_note(self):
        note = StickyNote(self)
        self.notes[note.note_id] = note
        self.schedule_save()
        return note

    def remove_note(self, note_id):
        if note_id in self.notes:
            del self.notes[note_id]
            self.schedule_save()

    def show_all_notes(self):
        for note in self.notes.values():
            note.show()
        self.root.deiconify()
        self.root.lift()

    def hide_all_notes(self):
        for note in self.notes.values():
            note.hide()

    def schedule_save(self):
        if self._save_timer:
            self.root.after_cancel(self._save_timer)
        self._save_timer = self.root.after(500, self.save_notes)

    def save_notes(self):
        data = [note.to_dict() for note in self.notes.values()]
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存失败: {e}")

    def load_notes(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"加载失败: {e}")
            return
        for item in data:
            note = StickyNote(
                self,
                note_id=item.get("id"),
                x=item.get("x"),
                y=item.get("y"),
                width=item.get("width", DEFAULT_WIDTH),
                height=item.get("height", DEFAULT_HEIGHT),
                content=item.get("content", "")
            )
            self.notes[note.note_id] = note

    def quit_app(self):
        self.save_notes()
        for note in list(self.notes.values()):
            try:
                note.root.destroy()
            except tk.TclError:
                pass
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = NoteApp()
    app.run()

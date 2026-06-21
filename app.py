import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import json
import os
import uuid
import threading
import pystray
from PIL import Image, ImageDraw

try:
    import keyboard
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")
MIN_WIDTH = 150
MIN_HEIGHT = 120
DEFAULT_WIDTH = 220
DEFAULT_HEIGHT = 220
HEADER_HEIGHT = 28
AUTO_SAVE_INTERVAL = 30000
TEXT_FG = "#212121"
PIN_FG = "#C62828"
FONT_FAMILY = "Microsoft YaHei"
FONT_SIZE = 10

COLORS = {
    "yellow": {"name": "黄", "bg": "#FFF9C4", "header": "#FDD835", "border": "#F9A825"},
    "pink":   {"name": "粉", "bg": "#FCE4EC", "header": "#F48FB1", "border": "#AD1457"},
    "blue":   {"name": "蓝", "bg": "#E3F2FD", "header": "#64B5F6", "border": "#1565C0"},
    "green":  {"name": "绿", "bg": "#E8F5E9", "header": "#81C784", "border": "#2E7D32"},
    "white":  {"name": "白", "bg": "#FFFFFF", "header": "#E0E0E0", "border": "#616161"},
}
DEFAULT_COLOR = "yellow"


class StickyNote:
    def __init__(self, app, note_id=None, x=None, y=None, width=DEFAULT_WIDTH,
                 height=DEFAULT_HEIGHT, content="", color=None, tag="", pinned=False, bold_ranges=None):
        self.app = app
        self.note_id = note_id or str(uuid.uuid4())
        self.content = content
        self.width = max(width, MIN_WIDTH)
        self.height = max(height, MIN_HEIGHT)
        self.color_key = color if color in COLORS else DEFAULT_COLOR
        self.tag = tag or ""
        self.pinned = bool(pinned)
        self.bold_ranges = bold_ranges or []
        self._saved_flash = None

        self.root = tk.Toplevel(app.root)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", self.pinned)
        self.root.configure(bg=COLORS[self.color_key]["border"])
        self.root.resizable(False, False)
        self._user_resized = False

        if x is None or y is None:
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
        self._apply_pin_visual()
        self._restore_bold()
        self._bind_events()
        self.root.after(50, self._auto_resize_height)

    def _c(self, key):
        return COLORS[self.color_key][key]

    def _build_ui(self):
        border = self._c("border")
        header_bg = self._c("header")

        self.header = tk.Frame(self.root, bg=border, height=28)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.inner_header = tk.Frame(self.header, bg=header_bg)
        self.inner_header.pack(fill="both", expand=True, padx=2, pady=2)

        self.title_label = tk.Label(
            self.inner_header, text="便签", bg=header_bg, fg=TEXT_FG,
            font=(FONT_FAMILY, 9, "bold"), cursor="fleur"
        )
        self.title_label.pack(side="left", padx=6)

        self.tag_label = tk.Label(
            self.inner_header, text="", bg=header_bg, fg=TEXT_FG,
            font=(FONT_FAMILY, 8), padx=4, cursor="hand2"
        )
        self.tag_label.pack(side="left")
        self._refresh_tag_label()

        self.close_btn = tk.Label(
            self.inner_header, text="×", bg=header_bg, fg=PIN_FG,
            font=("Arial", 14, "bold"), cursor="hand2", padx=6
        )
        self.close_btn.pack(side="right")

        self.text = scrolledtext.ScrolledText(
            self.root, bg=self._c("bg"), fg=TEXT_FG, bd=0,
            font=(FONT_FAMILY, FONT_SIZE), wrap="word",
            highlightthickness=0, insertbackground=TEXT_FG,
            padx=6, pady=4
        )
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("bold", font=(FONT_FAMILY, FONT_SIZE, "bold"))
        self.text.insert("1.0", self.content)

        self.resize_handle = tk.Label(
            self.root, text="⇲", bg=self._c("bg"), fg="#9E9E9E",
            font=("Arial", 10), cursor="size_nw_se"
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)

    def _refresh_tag_label(self):
        if self.tag:
            self.tag_label.config(text=f"#{self.tag}")
        else:
            self.tag_label.config(text="")

    def _apply_pin_visual(self):
        if self.pinned:
            self.root.configure(bg=PIN_FG)
            self.header.configure(bg=PIN_FG)
            self.title_label.config(text="📌 便签", fg=PIN_FG, bg=self._c("header"))
        else:
            self.root.configure(bg=self._c("border"))
            self.header.configure(bg=self._c("border"))
            self.title_label.config(text="便签", fg=TEXT_FG, bg=self._c("header"))
        try:
            self.root.attributes("-topmost", self.pinned)
        except tk.TclError:
            pass

    def _restore_bold(self):
        for s, e in self.bold_ranges:
            try:
                self.text.tag_add("bold", s, e)
            except tk.TclError:
                pass

    def _bind_events(self):
        for w in (self.header, self.inner_header, self.title_label, self.tag_label):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<Button-3>", self._show_context_menu)

        self.text.bind("<Button-3>", self._show_context_menu)
        self.close_btn.bind("<Button-1>", lambda e: self.destroy())

        self.resize_handle.bind("<Button-1>", self._start_resize)
        self.resize_handle.bind("<B1-Motion>", self._on_resize)

        self.text.bind("<KeyRelease>", self._on_text_change)
        self.root.bind("<Configure>", lambda e: self.app.schedule_save())
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.text.bind("<FocusOut>", self._on_focus_out)

        self.text.bind("<Control-s>", self._manual_save)
        self.text.bind("<Control-S>", self._manual_save)
        self.text.bind("<Control-b>", self._toggle_bold)
        self.text.bind("<Control-B>", self._toggle_bold)

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
        self._user_resized = True
        dw = event.x_root - self._resize_x
        dh = event.y_root - self._resize_y
        new_w = max(MIN_WIDTH, self._resize_w + dw)
        new_h = max(MIN_HEIGHT, self._resize_h + dh)
        self.root.geometry(f"{new_w}x{new_h}")

    def _on_text_change(self, event=None):
        self.app.schedule_save()
        self._auto_resize_height()

    def _on_focus_out(self, event=None):
        self.root.after(100, self._check_focus_and_save)

    def _check_focus_and_save(self):
        try:
            focused = self.root.focus_get()
            root_path = str(self.root)
            if focused is None or not str(focused).startswith(root_path):
                self.app.save_notes()
        except tk.TclError:
            pass

    def _auto_resize_height(self):
        if self._user_resized:
            return
        try:
            line_count = int(self.text.index("end-1c").split(".")[0])
            char_height = self.text.metrics("linespace")
            pad_top = int(self.text.cget("pady"))
            pad_bottom = pad_top
            border = 4
            text_height = line_count * char_height + pad_top + pad_bottom + border
            total_height = HEADER_HEIGHT + text_height + 24
            current_h = self.root.winfo_height()
            min_h = max(MIN_HEIGHT, self.height)
            new_h = max(min_h, total_height)
            if new_h != current_h:
                current_g = self.root.geometry()
                size_part = current_g.split("+")[0]
                pos_part = "+" + "+".join(current_g.split("+")[1:])
                w = int(size_part.split("x")[0])
                self.root.geometry(f"{w}x{new_h}{pos_part}")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _manual_save(self, event=None):
        self.app.save_notes()
        self._flash_saved()
        return "break"

    def _flash_saved(self):
        try:
            original = self.title_label.cget("text")
            self.title_label.config(text="✓ 已保存")
            if self._saved_flash:
                self.root.after_cancel(self._saved_flash)
            self._saved_flash = self.root.after(800, lambda: self.title_label.config(text=original))
        except tk.TclError:
            pass

    def _toggle_bold(self, event=None):
        try:
            if self.text.tag_ranges("sel"):
                tags_at_first = self.text.tag_names("sel.first")
                if "bold" in tags_at_first:
                    self.text.tag_remove("bold", "sel.first", "sel.last")
                else:
                    self.text.tag_add("bold", "sel.first", "sel.last")
        except tk.TclError:
            pass
        self.app.schedule_save()
        return "break"

    def _show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, font=(FONT_FAMILY, 9))
        menu.add_checkbutton(label="置顶", command=self.toggle_pin,
                             variable=tk.BooleanVar(value=self.pinned))
        menu.add_command(label="设置标签...", command=self._set_tag_dialog)
        color_menu = tk.Menu(menu, tearoff=0, font=(FONT_FAMILY, 9))
        for key in COLORS:
            color_menu.add_command(
                label=COLORS[key]["name"],
                command=lambda k=key: self.set_color(k)
            )
        menu.add_cascade(label="颜色", menu=color_menu)
        menu.add_separator()
        menu.add_command(label="删除便签", command=self.destroy)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def toggle_pin(self):
        self.pinned = not self.pinned
        self._apply_pin_visual()
        self.app.schedule_save()

    def _set_tag_dialog(self):
        new_tag = simpledialog.askstring(
            "设置标签", "输入标签名称（留空清除）：", initialvalue=self.tag, parent=self.app.root
        )
        if new_tag is not None:
            self.tag = new_tag.strip()
            self._refresh_tag_label()
            self.app.schedule_save()

    def set_color(self, color_key):
        if color_key not in COLORS:
            return
        self.color_key = color_key
        bg = self._c("bg")
        header_bg = self._c("header")
        self.text.config(bg=bg)
        self.resize_handle.config(bg=bg)
        self.inner_header.config(bg=header_bg)
        self.title_label.config(bg=header_bg)
        self.tag_label.config(bg=header_bg)
        self.close_btn.config(bg=header_bg)
        self._apply_pin_visual()
        self.app.schedule_save()

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

    def _get_bold_ranges(self):
        ranges = []
        start = "1.0"
        while True:
            rng = self.text.tag_nextrange("bold", start)
            if not rng:
                break
            s, e = rng
            ranges.append([self.text.index(s), self.text.index(e)])
            start = e
        return ranges

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
            "x": x, "y": y, "width": w, "height": h,
            "content": content,
            "color": self.color_key,
            "tag": self.tag,
            "pinned": self.pinned,
            "bold_ranges": self._get_bold_ranges()
        }


class ControlPanel:
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.root.title("桌面便签")
        self.root.geometry("260x200+50+50")
        self.root.resizable(False, False)
        self.root.configure(bg="#FAFAFA")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        frame = tk.Frame(self.root, bg="#FAFAFA")
        frame.pack(expand=True, fill="both", padx=20, pady=12)

        tk.Label(
            frame, text="桌面便签", bg="#FAFAFA", fg=TEXT_FG,
            font=(FONT_FAMILY, 12, "bold")
        ).pack(pady=(0, 6))

        color_frame = tk.Frame(frame, bg="#FAFAFA")
        color_frame.pack(fill="x", pady=(0, 8))
        tk.Label(color_frame, text="颜色：", bg="#FAFAFA", fg=TEXT_FG,
                font=(FONT_FAMILY, 9)).pack(side="left")
        self.color_buttons = {}
        for key in COLORS:
            btn = tk.Button(
                color_frame, width=2, height=1, relief="flat", bd=1,
                bg=COLORS[key]["bg"], activebackground=COLORS[key]["bg"],
                highlightthickness=2, highlightbackground="#BDBDBD",
                command=lambda k=key: self._select_color(k)
            )
            btn.pack(side="left", padx=3)
            self.color_buttons[key] = btn
        self._select_color(DEFAULT_COLOR)

        btn_frame = tk.Frame(frame, bg="#FAFAFA")
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame, text="新建便签", command=self.app.create_note,
            bg=COLORS[DEFAULT_COLOR]["header"], fg=TEXT_FG, bd=0, padx=16, pady=6,
            font=(FONT_FAMILY, 9, "bold"), cursor="hand2",
            activebackground="#FBC02D"
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        tk.Button(
            btn_frame, text="显示全部", command=self.app.show_all_notes,
            bg="#ECEFF1", fg=TEXT_FG, bd=0, padx=16, pady=6,
            font=(FONT_FAMILY, 9), cursor="hand2", activebackground="#CFD8DC"
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        hint = "Ctrl+Shift+N 新建 · Ctrl+S 保存 · Ctrl+B 加粗"
        if not HAS_KEYBOARD:
            hint = "提示：未安装 keyboard 库，全局快捷键不可用"
        tk.Label(
            frame, text=hint, bg="#FAFAFA", fg="#9E9E9E",
            font=(FONT_FAMILY, 8), wraplength=220, justify="left"
        ).pack(side="bottom", pady=(8, 0))

    def _select_color(self, key):
        self.app.current_color = key
        for k, btn in self.color_buttons.items():
            btn.config(highlightbackground=PIN_FG if k == key else "#BDBDBD",
                       relief="sunken" if k == key else "flat")

    def _on_close(self):
        self.app.minimize_to_tray()


class NoteApp:
    def __init__(self):
        self.root = tk.Tk()
        self.notes = {}
        self.current_color = DEFAULT_COLOR
        self._save_timer = None
        self._tray_icon = None
        self._tray_thread = None

        self.control = ControlPanel(self)
        self.load_notes()
        self.root.after(300, self._start_tray)
        self.root.after(500, self._auto_save_loop)
        self._register_hotkeys()

    def _register_hotkeys(self):
        if not HAS_KEYBOARD:
            return
        try:
            keyboard.add_hotkey("ctrl+shift+n", self._hotkey_new_note, suppress=False)
        except Exception as e:
            print(f"全局快捷键注册失败: {e}")

    def _hotkey_new_note(self):
        self.root.after(0, self.create_note)

    def _start_tray(self):
        self._tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        self._tray_thread.start()

    def _create_icon_image(self):
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([4, 6, size - 6, size - 4], fill=COLORS["yellow"]["bg"],
                       outline=COLORS["yellow"]["border"], width=2)
        draw.rectangle([4, 6, size - 6, 18], fill=COLORS["yellow"]["header"])
        for y in [26, 36, 46]:
            draw.line([(10, y), (size - 12, y)], fill="#BDBDBD", width=2)
        return img

    def _build_tray_menu(self):
        items = [
            pystray.MenuItem("新建便签", self._tray_new_note, default=True),
            pystray.MenuItem("显示所有便签", self._tray_show_all),
        ]
        tags = sorted({n.tag for n in self.notes.values() if n.tag})
        if tags or any(True for n in self.notes.values()):
            sub_items = [
                pystray.MenuItem("全部便签", self._tray_show_all),
                pystray.MenuItem("无标签", lambda icon, item: self.root.after(0, lambda: self.filter_by_tag(None))),
            ]
            if tags:
                sub_items.append(pystray.Menu.SEPARATOR)
                for t in tags:
                    sub_items.append(
                        pystray.MenuItem(t, lambda icon, item, t=t: self.root.after(0, lambda: self.filter_by_tag(t)))
                    )
            items.append(pystray.MenuItem("按标签筛选", None, submenu=pystray.Menu(*sub_items)))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("退出", self._tray_quit))
        return pystray.Menu(*items)

    def _run_tray(self):
        self._tray_icon = pystray.Icon(
            "sticky_notes", self._create_icon_image(), "桌面便签", self._build_tray_menu
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
        note = StickyNote(self, color=self.current_color)
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

    def filter_by_tag(self, tag):
        for note in self.notes.values():
            if tag is None:
                if not note.tag:
                    note.show()
                else:
                    note.hide()
            else:
                if note.tag == tag:
                    note.show()
                else:
                    note.hide()
        self.root.deiconify()
        self.root.lift()

    def schedule_save(self):
        if self._save_timer:
            self.root.after_cancel(self._save_timer)
        self._save_timer = self.root.after(500, self.save_notes)

    def _auto_save_loop(self):
        try:
            self.save_notes()
        except Exception:
            pass
        self.root.after(AUTO_SAVE_INTERVAL, self._auto_save_loop)

    def save_notes(self):
        data = [note.to_dict() for note in self.notes.values()]
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存失败: {e}")
        if self._tray_icon is not None:
            try:
                self._tray_icon.update_menu()
            except Exception:
                pass

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
                x=item.get("x"), y=item.get("y"),
                width=item.get("width", DEFAULT_WIDTH),
                height=item.get("height", DEFAULT_HEIGHT),
                content=item.get("content", ""),
                color=item.get("color", DEFAULT_COLOR),
                tag=item.get("tag", ""),
                pinned=item.get("pinned", False),
                bold_ranges=item.get("bold_ranges", []),
            )
            self.notes[note.note_id] = note

    def quit_app(self):
        self.save_notes()
        if HAS_KEYBOARD:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
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

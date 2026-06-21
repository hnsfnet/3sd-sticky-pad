import uuid
import tkinter as tk
from tkinter import scrolledtext, simpledialog

import config


class StickyNote:
    def __init__(self, manager, note_id=None, x=None, y=None,
                 width=config.DEFAULT_WIDTH, height=config.DEFAULT_HEIGHT,
                 content="", color=None, tag="", pinned=False, bold_ranges=None):
        self.manager = manager
        self.note_id = note_id or str(uuid.uuid4())
        self.content = content
        self.width = max(width, config.MIN_WIDTH)
        self.height = max(height, config.MIN_HEIGHT)
        self.color_key = color if color in config.COLORS else config.DEFAULT_COLOR
        self.tag = tag or ""
        self.pinned = bool(pinned)
        self.bold_ranges = bold_ranges or []
        self._saved_flash = None
        self._user_resized = False

        self.root = tk.Toplevel(manager.root)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", self.pinned)
        self.root.configure(bg=self._c("border"))
        self.root.resizable(False, False)

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
        return config.COLORS[self.color_key][key]

    def _build_ui(self):
        border = self._c("border")
        header_bg = self._c("header")

        self.header = tk.Frame(self.root, bg=border, height=config.HEADER_HEIGHT)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.inner_header = tk.Frame(self.header, bg=header_bg)
        self.inner_header.pack(fill="both", expand=True, padx=2, pady=2)

        self.title_label = tk.Label(
            self.inner_header, text="便签", bg=header_bg, fg=config.TEXT_FG,
            font=(config.FONT_FAMILY, config.HEADER_FONT_SIZE, "bold"), cursor="fleur"
        )
        self.title_label.pack(side="left", padx=6)

        self.tag_label = tk.Label(
            self.inner_header, text="", bg=header_bg, fg=config.TEXT_FG,
            font=(config.FONT_FAMILY, config.TAG_FONT_SIZE), padx=4, cursor="hand2"
        )
        self.tag_label.pack(side="left")
        self._refresh_tag_label()

        self.close_btn = tk.Label(
            self.inner_header, text="×", bg=header_bg, fg=config.PIN_FG,
            font=("Arial", 14, "bold"), cursor="hand2", padx=6
        )
        self.close_btn.pack(side="right")

        self.text = scrolledtext.ScrolledText(
            self.root, bg=self._c("bg"), fg=config.TEXT_FG, bd=0,
            font=(config.FONT_FAMILY, config.FONT_SIZE), wrap="word",
            highlightthickness=0, insertbackground=config.TEXT_FG,
            padx=6, pady=4
        )
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("bold", font=(config.FONT_FAMILY, config.FONT_SIZE, "bold"))
        self.text.insert("1.0", self.content)

        self.resize_handle = tk.Label(
            self.root, text="⇲", bg=self._c("bg"), fg="#9E9E9E",
            font=("Arial", 10), cursor="size_nw_se"
        )
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)

    def _refresh_tag_label(self):
        self.tag_label.config(text=f"#{self.tag}" if self.tag else "")

    def _apply_pin_visual(self):
        if self.pinned:
            self.root.configure(bg=config.PIN_FG)
            self.header.configure(bg=config.PIN_FG)
            self.title_label.config(text="📌 便签", fg=config.PIN_FG, bg=self._c("header"))
        else:
            self.root.configure(bg=self._c("border"))
            self.header.configure(bg=self._c("border"))
            self.title_label.config(text="便签", fg=config.TEXT_FG, bg=self._c("header"))
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
        self.root.bind("<Configure>", lambda e: self.manager.schedule_save())
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
        new_w = max(config.MIN_WIDTH, self._resize_w + dw)
        new_h = max(config.MIN_HEIGHT, self._resize_h + dh)
        self.root.geometry(f"{new_w}x{new_h}")

    def _on_text_change(self, event=None):
        self.manager.schedule_save()
        self._auto_resize_height()

    def _on_focus_out(self, event=None):
        self.root.after(100, self._check_focus_and_save)

    def _check_focus_and_save(self):
        try:
            focused = self.root.focus_get()
            root_path = str(self.root)
            if focused is None or not str(focused).startswith(root_path):
                self.manager.save_now()
        except tk.TclError:
            pass

    def _auto_resize_height(self):
        if self._user_resized:
            return
        try:
            line_count = int(self.text.index("end-1c").split(".")[0])
            char_height = self.text.metrics("linespace")
            pad_top = int(self.text.cget("pady"))
            border = 4
            text_height = line_count * char_height + pad_top * 2 + border
            total_height = config.HEADER_HEIGHT + text_height + 24
            current_h = self.root.winfo_height()
            min_h = max(config.MIN_HEIGHT, self.height)
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
        self.manager.save_now()
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
        self.manager.schedule_save()
        return "break"

    def _show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, font=(config.FONT_FAMILY, config.HEADER_FONT_SIZE))
        menu.add_checkbutton(label="置顶", command=self.toggle_pin,
                             variable=tk.BooleanVar(value=self.pinned))
        menu.add_command(label="设置标签...", command=self._set_tag_dialog)
        color_menu = tk.Menu(menu, tearoff=0, font=(config.FONT_FAMILY, config.HEADER_FONT_SIZE))
        for key in config.COLORS:
            color_menu.add_command(
                label=config.COLORS[key]["name"],
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
        self.manager.schedule_save()

    def _set_tag_dialog(self):
        new_tag = simpledialog.askstring(
            "设置标签", "输入标签名称（留空清除）：", initialvalue=self.tag, parent=self.manager.root
        )
        if new_tag is not None:
            self.tag = new_tag.strip()
            self._refresh_tag_label()
            self.manager.schedule_save()

    def set_color(self, color_key):
        if color_key not in config.COLORS:
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
        self.manager.schedule_save()

    def destroy(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.manager.remove_note(self.note_id)

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

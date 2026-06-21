import tkinter as tk

import config
from note_window import StickyNote
from persistence import NoteStore


class NoteManager:
    def __init__(self, root, store=None):
        self.root = root
        self.notes = {}
        self.current_color = config.DEFAULT_COLOR
        self.store = store or NoteStore()
        self._save_timer = None
        self.on_saved = None

    def create_note(self, color=None):
        note = StickyNote(self, color=color or self.current_color)
        self.notes[note.note_id] = note
        self.schedule_save()
        return note

    def remove_note(self, note_id):
        if note_id in self.notes:
            del self.notes[note_id]
            self.schedule_save()

    def show_all(self):
        for note in self.notes.values():
            note.show()
        self.root.deiconify()
        self.root.lift()

    def hide_all(self):
        for note in self.notes.values():
            note.hide()

    def filter_by_tag(self, tag):
        for note in self.notes.values():
            if tag is None:
                note.show() if not note.tag else note.hide()
            else:
                note.show() if note.tag == tag else note.hide()
        self.root.deiconify()
        self.root.lift()

    def get_tags(self):
        return sorted({n.tag for n in self.notes.values() if n.tag})

    def has_notes(self):
        return len(self.notes) > 0

    def schedule_save(self):
        if self._save_timer:
            self.root.after_cancel(self._save_timer)
        self._save_timer = self.root.after(config.DEBOUNCE_SAVE_DELAY, self.save_now)

    def save_now(self):
        data = [note.to_dict() for note in self.notes.values()]
        self.store.save(data)
        if self.on_saved:
            try:
                self.on_saved()
            except Exception:
                pass

    def start_auto_save(self):
        self.root.after(config.AUTO_SAVE_INTERVAL, self._auto_save_tick)

    def _auto_save_tick(self):
        try:
            self.save_now()
        except Exception:
            pass
        self.root.after(config.AUTO_SAVE_INTERVAL, self._auto_save_tick)

    def load(self):
        data = self.store.load()
        for item in data:
            note = StickyNote(
                self,
                note_id=item.get("id"),
                x=item.get("x"), y=item.get("y"),
                width=item.get("width", config.DEFAULT_WIDTH),
                height=item.get("height", config.DEFAULT_HEIGHT),
                content=item.get("content", ""),
                color=item.get("color", config.DEFAULT_COLOR),
                tag=item.get("tag", ""),
                pinned=item.get("pinned", False),
                bold_ranges=item.get("bold_ranges", []),
            )
            self.notes[note.note_id] = note

    def shutdown(self):
        self.save_now()
        for note in list(self.notes.values()):
            try:
                note.root.destroy()
            except tk.TclError:
                pass
        self.notes.clear()

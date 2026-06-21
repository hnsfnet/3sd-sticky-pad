import tkinter as tk

import config
from note_model import Note
from note_window import StickyNote
from persistence import NoteStore


class NoteManager:
    def __init__(self, root, store=None, window_class=None):
        self.root = root
        self.store = store or NoteStore()
        self.window_class = window_class or StickyNote
        self.notes = {}
        self._windows = {}
        self.current_color = config.DEFAULT_COLOR
        self._save_timer = None
        self.on_saved = None

    def add_note(self, note):
        if not isinstance(note, Note):
            note = Note.from_dict(note)
        self.notes[note.id] = note
        self.schedule_save()
        return note

    def create_note(self, color=None):
        note = Note(color=color or self.current_color)
        self.notes[note.id] = note
        window = self.window_class(self, note)
        self._windows[note.id] = window
        self.schedule_save()
        return note

    def remove_note(self, note_id):
        if note_id in self._windows:
            del self._windows[note_id]
        if note_id in self.notes:
            del self.notes[note_id]
            self.schedule_save()

    def get_note(self, note_id):
        return self.notes.get(note_id)

    def list_notes(self):
        return list(self.notes.values())

    def find_by_tag(self, tag):
        if tag is None:
            return [n for n in self.notes.values() if not n.tag]
        return [n for n in self.notes.values() if n.tag == tag]

    def get_tags(self):
        return sorted({n.tag for n in self.notes.values() if n.tag})

    def has_notes(self):
        return len(self.notes) > 0

    def get_window(self, note_id):
        return self._windows.get(note_id)

    def list_windows(self):
        return list(self._windows.values())

    def show_all(self):
        for win in self._windows.values():
            win.show()
        self.root.deiconify()
        self.root.lift()

    def hide_all(self):
        for win in self._windows.values():
            win.hide()

    def filter_by_tag(self, tag):
        for nid, note in self.notes.items():
            win = self._windows.get(nid)
            if win is None:
                continue
            if tag is None:
                win.show() if not note.tag else win.hide()
            else:
                win.show() if note.tag == tag else win.hide()
        self.root.deiconify()
        self.root.lift()

    def schedule_save(self):
        if self._save_timer:
            self.root.after_cancel(self._save_timer)
        self._save_timer = self.root.after(config.DEBOUNCE_SAVE_DELAY, self.save_now)

    def save_now(self):
        data = list(self.notes.values())
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
        for note in data:
            self.notes[note.id] = note
            window = self.window_class(self, note)
            self._windows[note.id] = window

    def shutdown(self):
        self.save_now()
        for win in list(self._windows.values()):
            try:
                win.root.destroy()
            except tk.TclError:
                pass
        self._windows.clear()
        self.notes.clear()

import unittest
import os
import tempfile
import shutil
from unittest.mock import MagicMock

import config
from note_model import Note
from note_manager import NoteManager
from persistence import NoteStore


class MockRoot:
    def after(self, ms, func):
        return "timer-id"

    def after_cancel(self, timer_id):
        pass


class MockWindow:
    def __init__(self, manager, note):
        self.manager = manager
        self.note = note
        self.visible = True
        self.root = MagicMock()

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class TestNoteManagerData(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "notes.json")
        store = NoteStore(self.tmpfile)
        self.manager = NoteManager(
            root=MockRoot(),
            store=store,
            window_class=MockWindow,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_note_increments_count(self):
        self.assertEqual(len(self.manager.list_notes()), 0)
        note = self.manager.add_note(Note(id="n1", content="测试"))
        self.assertEqual(len(self.manager.list_notes()), 1)
        self.assertEqual(note.id, "n1")

    def test_get_note_by_id(self):
        note = Note(id="find-me", content="找到我")
        self.manager.add_note(note)
        found = self.manager.get_note("find-me")
        self.assertIsNotNone(found)
        self.assertEqual(found.content, "找到我")

    def test_get_nonexistent_note_returns_none(self):
        self.assertIsNone(self.manager.get_note("no-such-id"))

    def test_remove_note_deletes_it(self):
        self.manager.add_note(Note(id="del"))
        self.assertEqual(len(self.manager.list_notes()), 1)
        self.manager.remove_note("del")
        self.assertEqual(len(self.manager.list_notes()), 0)
        self.assertIsNone(self.manager.get_note("del"))

    def test_list_notes_returns_all(self):
        self.manager.add_note(Note(id="a"))
        self.manager.add_note(Note(id="b"))
        self.manager.add_note(Note(id="c"))
        notes = self.manager.list_notes()
        self.assertEqual(len(notes), 3)
        ids = {n.id for n in notes}
        self.assertEqual(ids, {"a", "b", "c"})

    def test_find_by_tag_matches_exact(self):
        self.manager.add_note(Note(id="w1", tag="工作"))
        self.manager.add_note(Note(id="w2", tag="工作"))
        self.manager.add_note(Note(id="p1", tag="个人"))
        self.manager.add_note(Note(id="n1", tag=""))
        work_notes = self.manager.find_by_tag("工作")
        self.assertEqual(len(work_notes), 2)
        self.assertTrue(all(n.tag == "工作" for n in work_notes))

    def test_find_by_tag_none_finds_untagged(self):
        self.manager.add_note(Note(id="t1", tag="有标签"))
        self.manager.add_note(Note(id="t2", tag=""))
        self.manager.add_note(Note(id="t3"))
        untagged = self.manager.find_by_tag(None)
        self.assertEqual(len(untagged), 2)
        self.assertTrue(all(not n.tag for n in untagged))

    def test_get_tags_sorted_unique(self):
        self.manager.add_note(Note(id="a", tag="zebra"))
        self.manager.add_note(Note(id="b", tag="apple"))
        self.manager.add_note(Note(id="c", tag="apple"))
        self.manager.add_note(Note(id="d", tag=""))
        tags = self.manager.get_tags()
        self.assertEqual(tags, ["apple", "zebra"])

    def test_has_notes(self):
        self.assertFalse(self.manager.has_notes())
        self.manager.add_note(Note(id="x"))
        self.assertTrue(self.manager.has_notes())

    def test_add_note_from_dict(self):
        self.manager.add_note({"id": "from-dict", "content": "dict 加的", "tag": "test"})
        note = self.manager.get_note("from-dict")
        self.assertIsInstance(note, Note)
        self.assertEqual(note.content, "dict 加的")
        self.assertEqual(note.tag, "test")


class TestNoteManagerWithWindows(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "notes.json")
        store = NoteStore(self.tmpfile)
        self.manager = NoteManager(
            root=MockRoot(),
            store=store,
            window_class=MockWindow,
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_note_creates_window(self):
        note = self.manager.create_note(color="pink")
        self.assertIsNotNone(note)
        window = self.manager.get_window(note.id)
        self.assertIsNotNone(window)
        self.assertIsInstance(window, MockWindow)
        self.assertEqual(window.note.id, note.id)

    def test_create_note_uses_default_color(self):
        self.manager.current_color = "green"
        note = self.manager.create_note()
        self.assertEqual(note.color, "green")

    def test_remove_note_removes_window(self):
        note = self.manager.create_note()
        self.assertIsNotNone(self.manager.get_window(note.id))
        self.manager.remove_note(note.id)
        self.assertIsNone(self.manager.get_window(note.id))
        self.assertIsNone(self.manager.get_note(note.id))

    def test_list_windows(self):
        n1 = self.manager.create_note()
        n2 = self.manager.create_note()
        windows = self.manager.list_windows()
        self.assertEqual(len(windows), 2)
        window_ids = {w.note.id for w in windows}
        self.assertEqual(window_ids, {n1.id, n2.id})

    def test_show_all(self):
        self.manager.create_note()
        self.manager.create_note()
        for w in self.manager.list_windows():
            w.hide()
        self.manager.show_all()
        self.assertTrue(all(w.visible for w in self.manager.list_windows()))

    def test_hide_all(self):
        self.manager.create_note()
        self.manager.create_note()
        self.manager.hide_all()
        self.assertTrue(all(not w.visible for w in self.manager.list_windows()))

    def test_filter_by_tag_shows_matching_hides_others(self):
        n1 = self.manager.create_note()
        n2 = self.manager.create_note()
        n1.tag = "工作"
        n2.tag = "个人"
        self.manager.filter_by_tag("工作")
        self.assertTrue(self.manager.get_window(n1.id).visible)
        self.assertFalse(self.manager.get_window(n2.id).visible)


class TestNoteManagerPersistence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "notes.json")
        self.store = NoteStore(self.tmpfile)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_manager(self):
        return NoteManager(root=MockRoot(), store=self.store, window_class=MockWindow)

    def test_save_now_persists_notes(self):
        manager = self._make_manager()
        manager.add_note(Note(id="save-me", content="要保存的内容", tag="test"))
        manager.save_now()
        with open(self.tmpfile, "r", encoding="utf-8") as f:
            raw = __import__("json").load(f)
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["id"], "save-me")
        self.assertEqual(raw[0]["content"], "要保存的内容")

    def test_load_restores_notes(self):
        self.store.save([
            Note(id="load-1", content="note one", tag="a"),
            Note(id="load-2", content="note two", tag="b", pinned=True),
        ])
        manager = self._make_manager()
        manager.load()
        self.assertEqual(len(manager.list_notes()), 2)
        n1 = manager.get_note("load-1")
        self.assertEqual(n1.content, "note one")
        self.assertEqual(n1.tag, "a")
        n2 = manager.get_note("load-2")
        self.assertTrue(n2.pinned)
        self.assertEqual(len(manager.list_windows()), 2)

    def test_shutdown_saves_and_clears(self):
        manager = self._make_manager()
        manager.add_note(Note(id="shutdown-test", content="关机前保存"))
        manager.shutdown()
        self.assertEqual(len(manager.list_notes()), 0)
        self.assertEqual(len(manager.list_windows()), 0)
        reloaded = self.store.load()
        self.assertEqual(len(reloaded), 1)
        self.assertEqual(reloaded[0].id, "shutdown-test")


if __name__ == "__main__":
    unittest.main()

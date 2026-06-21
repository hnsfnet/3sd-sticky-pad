import unittest
import os
import json
import tempfile
import shutil

from note_model import Note
from persistence import NoteStore


class TestNoteStoreEmptyFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "notes.json")
        self.store = NoteStore(self.tmpfile)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_missing_file_returns_empty_list(self):
        self.assertFalse(os.path.exists(self.tmpfile))
        result = self.store.load()
        self.assertEqual(result, [])

    def test_empty_list_save_creates_file(self):
        self.store.save([])
        self.assertTrue(os.path.exists(self.tmpfile))
        with open(self.tmpfile, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, [])


class TestNoteStoreCorruptedFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "notes.json")
        self.store = NoteStore(self.tmpfile)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_invalid_json_returns_empty_list(self):
        with open(self.tmpfile, "w", encoding="utf-8") as f:
            f.write("{invalid json here!!")
        result = self.store.load()
        self.assertEqual(result, [])

    def test_non_list_json_returns_empty_list(self):
        with open(self.tmpfile, "w", encoding="utf-8") as f:
            f.write('{"foo": "bar"}')
        result = self.store.load()
        self.assertEqual(result, [])


class TestNoteStoreSaveAndLoad(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "notes.json")
        self.store = NoteStore(self.tmpfile)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_single_note_persists_to_disk(self):
        note = Note(id="note-1", content="hello world", color="pink", tag="work")
        self.store.save([note])
        self.assertTrue(os.path.exists(self.tmpfile))
        with open(self.tmpfile, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.assertEqual(len(raw), 1)
        self.assertEqual(raw[0]["id"], "note-1")
        self.assertEqual(raw[0]["content"], "hello world")
        self.assertEqual(raw[0]["color"], "pink")
        self.assertEqual(raw[0]["tag"], "work")

    def test_load_returns_note_objects(self):
        note = Note(id="abc", content="test", x=100, y=200, width=300, height=400)
        self.store.save([note])
        loaded = self.store.load()
        self.assertEqual(len(loaded), 1)
        self.assertIsInstance(loaded[0], Note)
        self.assertEqual(loaded[0].id, "abc")
        self.assertEqual(loaded[0].content, "test")
        self.assertEqual(loaded[0].x, 100)
        self.assertEqual(loaded[0].y, 200)
        self.assertEqual(loaded[0].width, 300)
        self.assertEqual(loaded[0].height, 400)

    def test_save_and_load_multiple_notes(self):
        notes = [
            Note(id="n1", content="第一条"),
            Note(id="n2", content="第二条", tag="personal"),
            Note(id="n3", content="第三条", pinned=True, color="green"),
        ]
        self.store.save(notes)
        loaded = self.store.load()
        self.assertEqual(len(loaded), 3)
        ids = {n.id for n in loaded}
        self.assertEqual(ids, {"n1", "n2", "n3"})
        n3 = next(n for n in loaded if n.id == "n3")
        self.assertTrue(n3.pinned)
        self.assertEqual(n3.color, "green")

    def test_roundtrip_preserves_unicode(self):
        note = Note(id="cn", content="中文便签测试 🌟", tag="工作")
        self.store.save([note])
        loaded = self.store.load()
        self.assertEqual(loaded[0].content, "中文便签测试 🌟")
        self.assertEqual(loaded[0].tag, "工作")

    def test_save_overwrites_previous_content(self):
        self.store.save([Note(id="old")])
        self.store.save([Note(id="new")])
        loaded = self.store.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].id, "new")

    def test_load_skips_non_dict_items(self):
        with open(self.tmpfile, "w", encoding="utf-8") as f:
            json.dump([{"id": "a", "content": "ok"}, "not_a_dict", 123], f)
        loaded = self.store.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].id, "a")


if __name__ == "__main__":
    unittest.main()

import unittest
import time

import config
from note_model import Note


class TestNoteCreation(unittest.TestCase):
    def test_default_values(self):
        note = Note()
        self.assertTrue(note.id)
        self.assertIsNone(note.x)
        self.assertIsNone(note.y)
        self.assertEqual(note.width, config.DEFAULT_WIDTH)
        self.assertEqual(note.height, config.DEFAULT_HEIGHT)
        self.assertEqual(note.content, "")
        self.assertEqual(note.color, config.DEFAULT_COLOR)
        self.assertEqual(note.tag, "")
        self.assertFalse(note.pinned)
        self.assertEqual(note.bold_ranges, [])
        self.assertIsInstance(note.created_at, float)
        self.assertIsInstance(note.updated_at, float)

    def test_custom_values(self):
        note = Note(
            id="abc-123",
            x=100, y=200,
            width=300, height=400,
            content="hello",
            color="pink",
            tag="work",
            pinned=True,
            bold_ranges=[["1.0", "1.5"]],
        )
        self.assertEqual(note.id, "abc-123")
        self.assertEqual(note.x, 100)
        self.assertEqual(note.y, 200)
        self.assertEqual(note.width, 300)
        self.assertEqual(note.height, 400)
        self.assertEqual(note.content, "hello")
        self.assertEqual(note.color, "pink")
        self.assertEqual(note.tag, "work")
        self.assertTrue(note.pinned)
        self.assertEqual(note.bold_ranges, [["1.0", "1.5"]])

    def test_timestamps_are_recent(self):
        before = time.time()
        note = Note()
        after = time.time()
        self.assertGreaterEqual(note.created_at, before)
        self.assertLessEqual(note.created_at, after)
        self.assertGreaterEqual(note.updated_at, before)
        self.assertLessEqual(note.updated_at, after)

    def test_touch_updates_updated_at(self):
        note = Note()
        old_updated = note.updated_at
        time.sleep(0.01)
        note.touch()
        self.assertGreater(note.updated_at, old_updated)
        self.assertEqual(note.created_at, note.created_at)


class TestNoteValidation(unittest.TestCase):
    def test_invalid_color_falls_back_to_default(self):
        note = Note(color="nonexistent")
        note.validate()
        self.assertEqual(note.color, config.DEFAULT_COLOR)

    def test_width_below_minimum_gets_floored(self):
        note = Note(width=50)
        note.validate()
        self.assertEqual(note.width, config.MIN_WIDTH)

    def test_height_below_minimum_gets_floored(self):
        note = Note(height=30)
        note.validate()
        self.assertEqual(note.height, config.MIN_HEIGHT)

    def test_none_tag_becomes_empty_string(self):
        note = Note(tag=None)
        note.validate()
        self.assertEqual(note.tag, "")

    def test_pinned_coerced_to_bool(self):
        note = Note(pinned=1)
        note.validate()
        self.assertTrue(note.pinned)
        note2 = Note(pinned=0)
        note2.validate()
        self.assertFalse(note2.pinned)

    def test_invalid_bold_ranges_reset(self):
        note = Note(bold_ranges="not-a-list")
        note.validate()
        self.assertEqual(note.bold_ranges, [])


class TestNoteSerialization(unittest.TestCase):
    def test_to_dict_contains_all_fields(self):
        note = Note(id="test-1", x=10, y=20, width=200, height=200,
                    content="hi", color="blue", tag="work", pinned=True,
                    bold_ranges=[["1.0", "2.0"]])
        d = note.to_dict()
        self.assertEqual(d["id"], "test-1")
        self.assertEqual(d["x"], 10)
        self.assertEqual(d["y"], 20)
        self.assertEqual(d["width"], 200)
        self.assertEqual(d["height"], 200)
        self.assertEqual(d["content"], "hi")
        self.assertEqual(d["color"], "blue")
        self.assertEqual(d["tag"], "work")
        self.assertTrue(d["pinned"])
        self.assertEqual(d["bold_ranges"], [["1.0", "2.0"]])
        self.assertIn("created_at", d)
        self.assertIn("updated_at", d)

    def test_from_dict_restores_values(self):
        data = {
            "id": "abc",
            "x": 50, "y": 60,
            "width": 250, "height": 300,
            "content": "world",
            "color": "green",
            "tag": "personal",
            "pinned": True,
            "bold_ranges": [],
            "created_at": 1000.0,
            "updated_at": 2000.0,
        }
        note = Note.from_dict(data)
        self.assertEqual(note.id, "abc")
        self.assertEqual(note.x, 50)
        self.assertEqual(note.y, 60)
        self.assertEqual(note.width, 250)
        self.assertEqual(note.height, 300)
        self.assertEqual(note.content, "world")
        self.assertEqual(note.color, "green")
        self.assertEqual(note.tag, "personal")
        self.assertTrue(note.pinned)
        self.assertEqual(note.created_at, 1000.0)
        self.assertEqual(note.updated_at, 2000.0)

    def test_from_dict_missing_fields_use_defaults(self):
        note = Note.from_dict({})
        self.assertTrue(note.id)
        self.assertEqual(note.content, "")
        self.assertEqual(note.color, config.DEFAULT_COLOR)
        self.assertEqual(note.width, config.DEFAULT_WIDTH)
        self.assertFalse(note.pinned)

    def test_roundtrip(self):
        original = Note(id="xyz", content="测试内容", tag="测试", color="pink",
                        x=1, y=2, width=100, height=100, pinned=True,
                        bold_ranges=[["1.0", "1.3"]])
        data = original.to_dict()
        restored = Note.from_dict(data)
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.content, original.content)
        self.assertEqual(restored.tag, original.tag)
        self.assertEqual(restored.color, original.color)
        self.assertEqual(restored.x, original.x)
        self.assertEqual(restored.y, original.y)
        self.assertEqual(restored.width, original.width)
        self.assertEqual(restored.height, original.height)
        self.assertEqual(restored.pinned, original.pinned)
        self.assertEqual(restored.bold_ranges, original.bold_ranges)


if __name__ == "__main__":
    unittest.main()

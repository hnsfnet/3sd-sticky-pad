import unittest

import config


class TestModuleConstants(unittest.TestCase):
    def test_colors_are_defined(self):
        self.assertIsInstance(config.COLORS, dict)
        self.assertGreaterEqual(len(config.COLORS), 5)

    def test_color_structure(self):
        for key in ("yellow", "pink", "blue", "green", "white"):
            self.assertIn(key, config.COLORS)
            c = config.COLORS[key]
            self.assertIn("name", c)
            self.assertIn("bg", c)
            self.assertIn("header", c)
            self.assertIn("border", c)

    def test_default_color_exists_in_colors(self):
        self.assertIn(config.DEFAULT_COLOR, config.COLORS)

    def test_dimensions_are_positive(self):
        self.assertGreater(config.MIN_WIDTH, 0)
        self.assertGreater(config.MIN_HEIGHT, 0)
        self.assertGreater(config.DEFAULT_WIDTH, config.MIN_WIDTH)
        self.assertGreater(config.DEFAULT_HEIGHT, config.MIN_HEIGHT)
        self.assertGreater(config.HEADER_HEIGHT, 0)

    def test_save_intervals_are_positive(self):
        self.assertGreater(config.DEBOUNCE_SAVE_DELAY, 0)
        self.assertGreater(config.AUTO_SAVE_INTERVAL, 0)

    def test_font_settings(self):
        self.assertTrue(config.FONT_FAMILY)
        self.assertGreater(config.FONT_SIZE, 0)

    def test_data_file_is_string(self):
        self.assertIsInstance(config.DATA_FILE, str)
        self.assertTrue(config.DATA_FILE)

    def test_hotkey_is_string(self):
        self.assertIsInstance(config.HOTKEY_NEW_NOTE, str)
        self.assertTrue(config.HOTKEY_NEW_NOTE)

    def test_panel_settings(self):
        self.assertTrue(config.PANEL_TITLE)
        self.assertTrue(config.PANEL_GEOMETRY)

    def test_hint_texts_exist(self):
        self.assertTrue(config.HINT_TEXT)
        self.assertTrue(config.HINT_NO_KEYBOARD)


class TestAppConfigDefaults(unittest.TestCase):
    def test_default_config_contains_all_keys(self):
        cfg = config.AppConfig()
        self.assertIn("data_file", cfg)
        self.assertIn("min_width", cfg)
        self.assertIn("min_height", cfg)
        self.assertIn("default_width", cfg)
        self.assertIn("default_height", cfg)
        self.assertIn("header_height", cfg)
        self.assertIn("debounce_save_delay", cfg)
        self.assertIn("auto_save_interval", cfg)
        self.assertIn("text_fg", cfg)
        self.assertIn("pin_fg", cfg)
        self.assertIn("panel_bg", cfg)
        self.assertIn("hint_fg", cfg)
        self.assertIn("border_default", cfg)
        self.assertIn("font_family", cfg)
        self.assertIn("font_size", cfg)
        self.assertIn("header_font_size", cfg)
        self.assertIn("title_font_size", cfg)
        self.assertIn("tag_font_size", cfg)
        self.assertIn("colors", cfg)
        self.assertIn("default_color", cfg)
        self.assertIn("hotkey_new_note", cfg)
        self.assertIn("panel_title", cfg)
        self.assertIn("panel_geometry", cfg)
        self.assertIn("new_note_active_bg", cfg)
        self.assertIn("show_all_btn_bg", cfg)
        self.assertIn("show_all_btn_active_bg", cfg)
        self.assertIn("hint_text", cfg)
        self.assertIn("hint_no_keyboard", cfg)

    def test_default_values_match_module_constants(self):
        cfg = config.AppConfig()
        self.assertEqual(cfg.min_width, config.MIN_WIDTH)
        self.assertEqual(cfg.min_height, config.MIN_HEIGHT)
        self.assertEqual(cfg.default_width, config.DEFAULT_WIDTH)
        self.assertEqual(cfg.default_height, config.DEFAULT_HEIGHT)
        self.assertEqual(cfg.header_height, config.HEADER_HEIGHT)
        self.assertEqual(cfg.debounce_save_delay, config.DEBOUNCE_SAVE_DELAY)
        self.assertEqual(cfg.auto_save_interval, config.AUTO_SAVE_INTERVAL)
        self.assertEqual(cfg.text_fg, config.TEXT_FG)
        self.assertEqual(cfg.pin_fg, config.PIN_FG)
        self.assertEqual(cfg.font_family, config.FONT_FAMILY)
        self.assertEqual(cfg.font_size, config.FONT_SIZE)
        self.assertEqual(cfg.default_color, config.DEFAULT_COLOR)
        self.assertEqual(cfg.hotkey_new_note, config.HOTKEY_NEW_NOTE)
        self.assertEqual(cfg.panel_title, config.PANEL_TITLE)
        self.assertEqual(cfg.panel_geometry, config.PANEL_GEOMETRY)

    def test_default_colors_match_module(self):
        cfg = config.AppConfig()
        self.assertEqual(cfg.colors, config.COLORS)
        self.assertEqual(len(cfg.colors), len(config.COLORS))

    def test_default_color_is_valid(self):
        cfg = config.AppConfig()
        self.assertIn(cfg.default_color, cfg.colors)


class TestAppConfigOverride(unittest.TestCase):
    def test_override_single_value(self):
        cfg = config.AppConfig()
        cfg.set("default_color", "pink")
        self.assertEqual(cfg.default_color, "pink")
        self.assertEqual(cfg["default_color"], "pink")

    def test_override_via_init(self):
        cfg = config.AppConfig({
            "default_width": 300,
            "default_height": 250,
            "font_size": 12,
        })
        self.assertEqual(cfg.default_width, 300)
        self.assertEqual(cfg.default_height, 250)
        self.assertEqual(cfg.font_size, 12)

    def test_override_via_update(self):
        cfg = config.AppConfig()
        cfg.update({"min_width": 200, "panel_title": "My Notes"})
        self.assertEqual(cfg.min_width, 200)
        self.assertEqual(cfg.panel_title, "My Notes")

    def test_override_via_setitem(self):
        cfg = config.AppConfig()
        cfg["auto_save_interval"] = 60000
        self.assertEqual(cfg.auto_save_interval, 60000)

    def test_overrides_dont_affect_other_values(self):
        cfg = config.AppConfig({"default_color": "green"})
        self.assertEqual(cfg.default_color, "green")
        self.assertEqual(cfg.min_width, config.MIN_WIDTH)
        self.assertEqual(cfg.font_family, config.FONT_FAMILY)
        self.assertEqual(cfg.auto_save_interval, config.AUTO_SAVE_INTERVAL)

    def test_update_ignores_unknown_keys(self):
        cfg = config.AppConfig()
        cfg.update({"nonexistent_key": "value", "default_width": 400})
        self.assertEqual(cfg.default_width, 400)
        self.assertFalse(cfg.has("nonexistent_key"))


class TestAppConfigMissingKeyDefaults(unittest.TestCase):
    def test_get_with_default_returns_default_for_missing(self):
        cfg = config.AppConfig()
        self.assertEqual(cfg.get("no_such_key", "fallback"), "fallback")

    def test_get_returns_value_for_existing(self):
        cfg = config.AppConfig()
        self.assertEqual(cfg.get("default_color"), config.DEFAULT_COLOR)
        self.assertEqual(cfg.get("default_color", "blue"), config.DEFAULT_COLOR)

    def test_getattr_raises_for_missing(self):
        cfg = config.AppConfig()
        with self.assertRaises(AttributeError):
            _ = cfg.nonexistent_attr

    def test_getitem_raises_for_missing(self):
        cfg = config.AppConfig()
        with self.assertRaises(KeyError):
            _ = cfg["missing_key"]

    def test_has_checks_existence(self):
        cfg = config.AppConfig()
        self.assertTrue(cfg.has("data_file"))
        self.assertFalse(cfg.has("does_not_exist"))


class TestAppConfigReset(unittest.TestCase):
    def test_reset_restores_defaults(self):
        cfg = config.AppConfig()
        cfg.set("default_width", 999)
        cfg.set("font_size", 99)
        self.assertEqual(cfg.default_width, 999)
        self.assertEqual(cfg.font_size, 99)
        cfg.reset()
        self.assertEqual(cfg.default_width, config.DEFAULT_WIDTH)
        self.assertEqual(cfg.font_size, config.FONT_SIZE)

    def test_reset_after_update(self):
        cfg = config.AppConfig({"min_width": 300, "min_height": 200})
        cfg.reset()
        self.assertEqual(cfg.min_width, config.MIN_WIDTH)
        self.assertEqual(cfg.min_height, config.MIN_HEIGHT)


class TestAppConfigDictLike(unittest.TestCase):
    def test_to_dict_returns_copy(self):
        cfg = config.AppConfig()
        d = cfg.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["default_color"], config.DEFAULT_COLOR)
        d["default_color"] = "blue"
        self.assertEqual(cfg.default_color, config.DEFAULT_COLOR)

    def test_items_iterates_all(self):
        cfg = config.AppConfig()
        keys = {k for k, v in cfg.items()}
        self.assertIn("data_file", keys)
        self.assertIn("colors", keys)
        self.assertIn("hint_text", keys)

    def test_keys_returns_all_keys(self):
        cfg = config.AppConfig()
        keys = list(cfg.keys())
        self.assertGreater(len(keys), 20)


if __name__ == "__main__":
    unittest.main()

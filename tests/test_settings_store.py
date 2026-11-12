import json
import os
import tempfile
import unittest
from unittest.mock import patch

from arisechan.storage.settings_store import (
    DEFAULT_PERSONA,
    SettingsError,
    load_preferences,
    save_persona,
    save_preferences,
)


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {"APPDATA": self.temp_dir.name})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def test_missing_file_uses_defaults(self):
        preferences = load_preferences()

        self.assertEqual(preferences["persona"], DEFAULT_PERSONA)
        self.assertTrue(preferences["follow_cursor"])
        self.assertTrue(preferences["animate_on_click"])
        self.assertTrue(preferences["greet_on_start"])
        self.assertEqual(preferences["ai_provider"], "ollama")
        self.assertEqual(preferences["ollama_model"], "qwen3:4b")

    def test_legacy_persona_file_receives_defaults_for_new_options(self):
        path = os.path.join(self.temp_dir.name, "AriseChan", "settings.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as settings_file:
            json.dump({"persona": "Новая личность"}, settings_file)

        preferences = load_preferences()

        self.assertEqual(preferences["persona"], "Новая личность")
        self.assertTrue(preferences["follow_cursor"])
        self.assertTrue(preferences["animate_on_click"])
        self.assertTrue(preferences["greet_on_start"])
        self.assertEqual(preferences["ai_provider"], "ollama")
        self.assertEqual(preferences["ollama_model"], "qwen3:4b")

    def test_preferences_round_trip(self):
        save_preferences(
            "Моя Arise",
            follow_cursor=False,
            animate_on_click=False,
            greet_on_start=True,
        )

        self.assertEqual(
            load_preferences(),
            {
                "persona": "Моя Arise",
                "follow_cursor": False,
                "animate_on_click": False,
                "greet_on_start": True,
                "ai_provider": "ollama",
                "ollama_model": "qwen3:4b",
            },
        )

    def test_persona_update_preserves_behavior_preferences(self):
        save_preferences(
            "Первая",
            follow_cursor=False,
            animate_on_click=True,
            greet_on_start=False,
        )

        save_persona("Вторая")

        self.assertEqual(
            load_preferences(),
            {
                "persona": "Вторая",
                "follow_cursor": False,
                "animate_on_click": True,
                "greet_on_start": False,
                "ai_provider": "ollama",
                "ollama_model": "qwen3:4b",
            },
        )

    def test_openai_provider_and_custom_model_are_saved(self):
        save_preferences(
            "Arise",
            follow_cursor=True,
            animate_on_click=True,
            greet_on_start=True,
            ai_provider="openai",
            ollama_model="qwen3:8b",
        )

        preferences = load_preferences()

        self.assertEqual(preferences["ai_provider"], "openai")
        self.assertEqual(preferences["ollama_model"], "qwen3:8b")

    def test_invalid_option_type_is_reported(self):
        path = os.path.join(self.temp_dir.name, "AriseChan", "settings.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as settings_file:
            json.dump(
                {"persona": "Arise", "follow_cursor": "yes"},
                settings_file,
            )

        with self.assertRaisesRegex(SettingsError, "follow_cursor"):
            load_preferences()


if __name__ == "__main__":
    unittest.main()

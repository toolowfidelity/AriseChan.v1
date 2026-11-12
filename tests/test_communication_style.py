import unittest

from arisechan.services.communication_style import build_system_prompt
from arisechan.storage.settings_store import DEFAULT_COMMUNICATION_STYLE


class CommunicationStyleTests(unittest.TestCase):
    def test_default_style_includes_concise_warm_instructions(self):
        prompt = build_system_prompt("Ты Arise.", DEFAULT_COMMUNICATION_STYLE)

        self.assertIn("1–3 предложениями", prompt)
        self.assertIn("тёплой и заботливой", prompt)
        self.assertIn("Шути редко", prompt)

    def test_style_values_change_prompt_behavior(self):
        prompt = build_system_prompt(
            "Ты Arise.",
            {
                "conciseness": 0,
                "warmth": 0,
                "humor": 100,
                "energy": 100,
            },
        )

        self.assertIn("подробно", prompt)
        self.assertIn("нейтральный тон", prompt)
        self.assertIn("Часто добавляй", prompt)
        self.assertIn("живо и энергично", prompt)


if __name__ == "__main__":
    unittest.main()

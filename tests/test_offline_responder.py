import unittest

from arisechan.services.offline_responder import (
    reply_to,
    reply_to_motion,
    reply_to_sequence,
)


class OfflineResponderTests(unittest.TestCase):
    def test_greeting_gets_a_conversational_response(self):
        response = reply_to("Привет")

        self.assertIn("Рада", response)
        self.assertGreater(len(response.split()), 20)

    def test_project_message_mentions_arisechan_context(self):
        response = reply_to("Давай обсудим проект")

        self.assertIn("AriseChan", response)
        self.assertIn("облачка", response)

    def test_unknown_message_is_acknowledged_and_length_limited(self):
        message = "слово " * 80
        response = reply_to(message)

        self.assertIn("Поняла тебя", response)
        self.assertIn("...", response)
        self.assertLess(len(response), len(message) + 500)

    def test_motion_reply_describes_the_selected_animation(self):
        response = reply_to_motion(16, randomly_selected=True)

        self.assertIn("жест №16", response)
        self.assertIn("со слезами", response)

    def test_composed_animation_reply_describes_the_sequence(self):
        response = reply_to_sequence("greeting")

        self.assertIn("составную анимацию", response)
        with self.assertRaises(ValueError):
            reply_to_sequence("missing")


if __name__ == "__main__":
    unittest.main()

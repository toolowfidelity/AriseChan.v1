import unittest
from unittest.mock import Mock

from arisechan.services.motion_commands import (
    MOTION_COUNT,
    MOTION_SEQUENCES,
    MotionCommand,
    format_motion_list,
    parse_motion_command,
)
from arisechan.ui.overlay import AriseOverlay


class MotionCommandTests(unittest.TestCase):
    def test_parses_numbered_russian_and_english_commands(self):
        self.assertEqual(
            parse_motion_command("Покажи движение № 7"),
            MotionCommand("play", 7),
        )
        self.assertEqual(
            parse_motion_command("/motion 2"),
            MotionCommand("play", 2),
        )

    def test_parses_list_random_and_idle_commands(self):
        self.assertEqual(
            parse_motion_command("список движений"),
            MotionCommand("list"),
        )
        self.assertEqual(
            parse_motion_command("сделай случайное движение"),
            MotionCommand("random"),
        )
        self.assertEqual(
            parse_motion_command("вернись в ожидание"),
            MotionCommand("idle"),
        )
        self.assertEqual(
            parse_motion_command("поздоровайся"),
            MotionCommand("sequence", sequence="greeting"),
        )

    def test_lists_every_numbered_haru_motion(self):
        motion_list = format_motion_list()

        self.assertIn("haru_g_m01", motion_list)
        self.assertIn(f"haru_g_m{MOTION_COUNT:02d}", motion_list)
        self.assertIn("движение 7", motion_list)
        self.assertIn("07 — повороты головы и движения рук", motion_list)
        self.assertIn("Составные анимации", motion_list)
        self.assertEqual(MOTION_SEQUENCES["greeting"], (23, 7))

    def test_motion_chat_command_runs_locally_without_random_reaction(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        overlay.is_responding = False
        overlay.composer_anchor = None
        overlay.history = []
        overlay.character_block = Mock()
        overlay.character_block.play_motion.return_value = True
        overlay._spawn_message_block = Mock()
        overlay._update_turn_bubble = Mock()
        overlay._set_status = Mock()

        overlay.submit_message("движение 7")

        overlay.character_block.play_motion.assert_called_once_with(7)
        overlay.character_block.play_reaction.assert_not_called()
        self.assertEqual(len(overlay.history), 2)
        self.assertIn("жест №07", overlay.history[1]["content"])
        self.assertIn("движения рук", overlay.history[1]["content"])
        overlay._spawn_message_block.assert_called_once_with(
            "assistant",
            "Ты: движение 7",
            animate=False,
        )

    def test_random_motion_reply_names_the_selected_gesture(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        overlay.composer_anchor = None
        overlay.history = []
        overlay.character_block = Mock()
        overlay.character_block.play_reaction.return_value = 7
        overlay._spawn_message_block = Mock()
        overlay._update_turn_bubble = Mock()
        overlay._set_status = Mock()

        overlay._handle_motion_command(
            "случайное движение",
            MotionCommand("random"),
        )

        self.assertIn("жест №07", overlay.history[1]["content"])
        self.assertIn("движения рук", overlay.history[1]["content"])
        overlay.character_block.play_reaction.assert_called_once_with()

    def test_sequence_command_plays_a_composed_motion(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        overlay.composer_anchor = None
        overlay.history = []
        overlay.character_block = Mock()
        overlay.character_block.play_sequence.return_value = True
        overlay._spawn_message_block = Mock()
        overlay._update_turn_bubble = Mock()
        overlay._set_status = Mock()

        overlay._handle_motion_command(
            "поздоровайся",
            MotionCommand("sequence", sequence="greeting"),
        )

        overlay.character_block.play_sequence.assert_called_once_with("greeting")
        self.assertIn("составную анимацию", overlay.history[1]["content"])

    def test_non_motion_message_is_not_intercepted(self):
        self.assertIsNone(parse_motion_command("Давай обсудим проект"))


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import Mock, patch

from arisechan.ui.blocks import (
    CHARACTER_HEIGHT,
    CHARACTER_RIGHT_MARGIN,
    CHARACTER_TASKBAR_OVERLAP,
    CHARACTER_WIDTH,
    ControlsBlock,
)
from arisechan.ui.overlay import AriseOverlay, _taskbar_top


class OverlayLifecycleTests(unittest.TestCase):
    def test_closing_controls_shuts_down_the_overlay(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        controls = object()
        overlay.controls_block = controls
        overlay.character_block = None
        overlay.message_blocks = []
        overlay.shutdown = Mock()

        overlay._controls_closed(controls)

        self.assertIsNone(overlay.controls_block)
        overlay.shutdown.assert_called_once_with()

    def test_closing_menu_does_not_exit_while_character_is_visible(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        controls = object()
        overlay.controls_block = controls
        overlay.character_block = object()
        overlay.message_blocks = []
        overlay.shutdown = Mock()

        overlay._controls_closed(controls)

        self.assertIsNone(overlay.controls_block)
        overlay.shutdown.assert_not_called()

    def test_menu_opens_on_opposite_side_of_character(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        overlay.screen_width = 1920
        overlay.screen_height = 1080
        overlay.taskbar_top = 1040

        right_x, right_y = overlay._controls_position(1400, 400)
        self.assertEqual(
            right_x,
            1400 - ControlsBlock.WIDTH - ControlsBlock.GAP,
        )
        self.assertEqual(
            right_y,
            400 + (CHARACTER_HEIGHT - ControlsBlock.HEIGHT) // 2,
        )

        left_x, _ = overlay._controls_position(100, 400)
        self.assertEqual(
            left_x,
            100 + CHARACTER_WIDTH + ControlsBlock.GAP,
        )

    def test_character_feet_align_with_taskbar_and_right_margin_is_preserved(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        overlay.screen_width = 1920
        overlay.taskbar_top = 1040

        x, y = overlay._default_character_position()

        self.assertEqual(
            x + CHARACTER_WIDTH,
            overlay.screen_width - CHARACTER_RIGHT_MARGIN,
        )
        self.assertEqual(
            y + CHARACTER_HEIGHT,
            overlay.taskbar_top + CHARACTER_TASKBAR_OVERLAP,
        )

    def test_character_dimensions_are_larger_than_the_previous_size(self):
        self.assertGreater(CHARACTER_WIDTH, 360)
        self.assertGreater(CHARACTER_HEIGHT, 432)

    def test_taskbar_lookup_falls_back_to_screen_bottom_off_windows(self):
        with patch("arisechan.ui.overlay.sys.platform", "linux"):
            self.assertEqual(_taskbar_top(900), 900)


if __name__ == "__main__":
    unittest.main()

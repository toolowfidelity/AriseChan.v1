import unittest
from unittest.mock import Mock, patch

from arisechan.ui.blocks import (
    BUBBLE_INPUT_HEIGHT,
    CHARACTER_HEIGHT,
    CHARACTER_WIDTH,
    MessageBubbleBlock,
)
from arisechan.ui.bubble_layout import (
    CHARACTER_MOUTH_X_RATIO,
    CHARACTER_MOUTH_Y_RATIO,
    bubble_height,
    find_bubble_position,
    wrap_text,
)
from arisechan.ui.overlay import (
    BUBBLE_TAIL_EXTENSION,
    BUBBLE_WIDTH,
    AriseOverlay,
)


class FixedWidthFont:
    def measure(self, text):
        return len(text) * 8

    def metrics(self, _metric):
        return 16


class BubbleLayoutTests(unittest.TestCase):
    def setUp(self):
        self.overlay = AriseOverlay.__new__(AriseOverlay)
        self.overlay.message_font = FixedWidthFont()

    def test_long_words_are_split_to_fit_the_bubble(self):
        text = "abcdefghi"

        lines = wrap_text(text, self.overlay.message_font, 40)

        self.assertEqual("".join(lines), text)
        self.assertTrue(
            all(self.overlay.message_font.measure(line) <= 40 for line in lines)
        )

    def test_wrapping_keeps_spaces_between_words(self):
        text = "one two"

        self.assertEqual(
            " ".join(wrap_text(text, self.overlay.message_font, 40)),
            text,
        )

    def test_bubble_height_keeps_vertical_text_padding(self):
        lines = ["first", "second"]

        self.assertEqual(bubble_height(lines, self.overlay.message_font), 80)

    def test_bubble_is_centered_at_character_mouth_height(self):
        self.overlay.screen_width = 1920
        self.overlay.screen_height = 1080
        self.overlay.character_block = Mock()
        self.overlay.character_block.exists.return_value = True
        self.overlay.character_block.position.return_value = (1500, 600)
        bubble_height = 100

        width = BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION
        x, y = find_bubble_position(
            width,
            bubble_height,
            self.overlay.character_block,
            self.overlay.screen_width,
            self.overlay.screen_height,
            None,
        )

        mouth_x = 1500 + round(CHARACTER_WIDTH * CHARACTER_MOUTH_X_RATIO)
        self.assertEqual(x + width - 1, mouth_x)
        self.assertEqual(
            y + bubble_height // 2,
            600 + round(CHARACTER_HEIGHT * CHARACTER_MOUTH_Y_RATIO),
        )

    def test_bubble_stays_centered_when_character_is_hidden(self):
        self.overlay.screen_width = 1920
        self.overlay.screen_height = 1080
        self.overlay.character_block = None
        bubble_width = 292
        bubble_height = 100

        x, y = find_bubble_position(
            bubble_width,
            bubble_height,
            None,
            self.overlay.screen_width,
            self.overlay.screen_height,
        )

        self.assertEqual(x, (1920 - bubble_width) // 2)
        self.assertEqual(y, (1080 - bubble_height) // 2)

    def test_assistant_bubble_stays_anchored_when_nearby_blocks_overlap(self):
        self.overlay.screen_width = 1920
        self.overlay.screen_height = 1080
        self.overlay.taskbar_top = 1040
        self.overlay.character_block = Mock()
        self.overlay.character_block.exists.return_value = True
        self.overlay.character_block.position.return_value = (1500, 600)
        bubble_height = 100
        width = BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION

        x, y = find_bubble_position(
            width,
            bubble_height,
            self.overlay.character_block,
            self.overlay.screen_width,
            self.overlay.screen_height,
            self.overlay.taskbar_top,
        )

        mouth_x = 1500 + round(CHARACTER_WIDTH * CHARACTER_MOUTH_X_RATIO)
        mouth_y = 600 + round(CHARACTER_HEIGHT * CHARACTER_MOUTH_Y_RATIO)
        self.assertEqual(x + width - 1, mouth_x)
        self.assertEqual(y + bubble_height // 2, mouth_y)

    def test_dragging_character_repositions_related_blocks(self):
        self.overlay.screen_width = 1920
        self.overlay.screen_height = 1080
        self.overlay.character_block = Mock()
        self.overlay.character_block.exists.return_value = True
        self.overlay.character_block.position.return_value = (1000, 400)
        self.overlay.controls_block = Mock()
        self.overlay.controls_block.exists.return_value = True
        bubble = Mock()
        bubble.width = BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION
        bubble.message_height = 80
        bubble.role = "assistant"
        self.overlay.message_blocks = [bubble]
        self.overlay.composer_anchor = bubble
        with patch(
            "arisechan.ui.overlay.find_bubble_position",
            return_value=(900, 500),
        ):
            self.overlay._character_moved()

        self.overlay.controls_block.move_to.assert_called_once_with(1060, 342)
        bubble.move_to.assert_called_once_with(900, 500)

    def test_new_messages_stack_below_previous_bubbles(self):
        self.overlay.screen_width = 1920
        self.overlay.screen_height = 1080
        self.overlay.taskbar_top = 1040
        self.overlay.character_block = Mock()
        self.overlay.character_block.exists.return_value = True
        self.overlay.character_block.position.return_value = (1500, 600)
        older_assistant = Mock(
            width=BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION,
            message_height=80,
            role="assistant",
        )
        new_assistant = Mock(
            width=BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION,
            message_height=100,
            role="assistant",
        )
        self.overlay.message_blocks = [older_assistant, new_assistant]

        self.overlay._layout_message_stack()

        older_assistant.move_to.assert_called_once_with(1310, 546)
        new_assistant.move_to.assert_called_once_with(1310, 638)

    def test_spawning_message_keeps_previous_bubbles_in_chat(self):
        self.overlay.character_block = None
        self.overlay.message_blocks = [Mock()]
        previous_bubble = self.overlay.message_blocks[0]
        self.overlay.composer_anchor = None
        self.overlay.screen_width = 1920
        self.overlay.screen_height = 1080
        self.overlay._layout_message_stack = Mock()
        new_bubble = Mock()

        with (
            patch(
                "arisechan.ui.overlay.find_bubble_position",
                return_value=(200, 300),
            ),
            patch(
                "arisechan.ui.overlay.MessageBubbleBlock",
                return_value=new_bubble,
            ),
        ):
            result = self.overlay._spawn_message_block(
                "assistant",
                "Привет",
                animate=False,
            )

        self.assertIs(result, new_bubble)
        self.assertEqual(self.overlay.message_blocks, [previous_bubble, new_bubble])
        previous_bubble.close.assert_not_called()
        self.overlay._layout_message_stack.assert_called_once_with()

    def test_user_text_and_reply_share_one_turn_bubble(self):
        self.overlay.message_font = FixedWidthFont()
        self.overlay.character_block = None
        self.overlay._layout_message_stack = Mock()
        bubble = Mock()
        bubble.exists.return_value = True

        updated = self.overlay._update_turn_bubble(
            bubble,
            "Привет",
            "Рада тебя видеть",
            animate=False,
        )

        self.assertIs(updated, bubble)
        self.assertEqual(
            bubble.update_content.call_args.args[0],
            "Ты: Привет\n\nАриша: Рада тебя видеть",
        )
        self.overlay._layout_message_stack.assert_called_once_with()

    def test_local_turn_updates_its_original_bubble(self):
        overlay = AriseOverlay.__new__(AriseOverlay)
        overlay.is_responding = False
        overlay.composer_anchor = None
        overlay.history = []
        overlay.character_block = None
        overlay.message_font = FixedWidthFont()
        overlay.screen_width = 1920
        overlay.screen_height = 1080
        overlay.taskbar_top = 1040
        overlay._layout_message_stack = Mock()
        overlay._set_status = Mock()
        overlay.root = Mock()
        bubble = Mock()
        bubble.exists.return_value = True
        overlay._spawn_message_block = Mock(return_value=bubble)

        with patch("arisechan.ui.overlay.load_api_key", return_value=None):
            overlay.submit_message("Привет")

        overlay._spawn_message_block.assert_called_once_with(
            "assistant",
            "Ты: Привет",
            animate=False,
        )
        _, callback, message, response, turn_bubble = overlay.root.after.call_args.args
        callback(message, response, turn_bubble)

        self.assertEqual(
            bubble.update_content.call_args.args[0].splitlines()[0],
            "Ты: Привет",
        )
        self.assertIn("Ариша:", bubble.update_content.call_args.args[0])
        overlay._spawn_message_block.assert_called_once()

    def test_starting_turn_does_not_create_a_user_bubble(self):
        self.overlay.composer_anchor = None
        self.overlay._spawn_message_block = Mock(return_value=Mock())

        self.overlay._start_turn_bubble("Привет")

        self.overlay._spawn_message_block.assert_called_once_with(
            "assistant",
            "Ты: Привет",
            animate=False,
        )

    def test_chat_history_is_capped(self):
        self.overlay.history = []

        for index in range(45):
            self.overlay._record_message("user", str(index))

        self.assertEqual(len(self.overlay.history), 40)
        self.assertEqual(self.overlay.history[0]["content"], "5")

    def test_opening_composer_expands_the_same_bubble(self):
        bubble = MessageBubbleBlock.__new__(MessageBubbleBlock)
        bubble.input_visible = False
        bubble.message_height = 80
        bubble.height = 80
        bubble.width = BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION
        bubble.x = 1300
        bubble.y = 300
        bubble.window = Mock()
        bubble.canvas = Mock()
        bubble._draw_bubble = Mock()
        bubble.entry = Mock()

        bubble.show_composer()

        self.assertTrue(bubble.input_visible)
        self.assertEqual(bubble.height, 80 + BUBBLE_INPUT_HEIGHT)
        bubble.window.geometry.assert_called_once_with(
            f"{bubble.width}x{bubble.height}+1300+300"
        )
        bubble._draw_bubble.assert_called_once_with()
        bubble.entry.focus_set.assert_called_once_with()

    def test_closing_inline_composer_restores_original_bubble_height(self):
        bubble = MessageBubbleBlock.__new__(MessageBubbleBlock)
        bubble.input_visible = True
        bubble.message_height = 80
        bubble.height = 80 + BUBBLE_INPUT_HEIGHT
        bubble.width = BUBBLE_WIDTH + BUBBLE_TAIL_EXTENSION
        bubble.x = 1300
        bubble.y = 300
        bubble.window = Mock()
        bubble.canvas = Mock()
        bubble._draw_bubble = Mock()
        input_frame = Mock()
        bubble.input_frame = input_frame

        bubble.hide_composer()

        self.assertFalse(bubble.input_visible)
        self.assertIsNone(bubble.input_frame)
        self.assertEqual(bubble.height, bubble.message_height)
        input_frame.destroy.assert_called_once_with()
        bubble._draw_bubble.assert_called_once_with()

    def test_opening_another_bubble_hides_previous_inline_input(self):
        first_bubble = Mock()
        second_bubble = Mock()
        self.overlay.composer_anchor = first_bubble

        self.overlay.open_composer(second_bubble)

        first_bubble.hide_composer.assert_called_once_with()
        second_bubble.show_composer.assert_called_once_with()
        self.assertIs(self.overlay.composer_anchor, second_bubble)

    def test_close_composer_hides_inline_input(self):
        bubble = Mock()
        self.overlay.composer_anchor = bubble

        self.overlay.close_composer()

        bubble.hide_composer.assert_called_once_with()
        self.assertIsNone(self.overlay.composer_anchor)

    def test_welcome_is_spawned_once_after_character_enters(self):
        self.overlay.welcome_shown = False
        self.overlay.character_block = None
        self.overlay._spawn_message_block = Mock()

        self.overlay._character_entered()
        self.overlay._character_entered()

        self.overlay._spawn_message_block.assert_called_once_with(
            "welcome",
            "Привет! Я Arise. Нажми на облачко, чтобы написать мне.",
            animate=False,
        )


if __name__ == "__main__":
    unittest.main()

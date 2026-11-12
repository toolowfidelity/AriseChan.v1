import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from arisechan.ui.blocks import CharacterBlock, FloatingBlock
from arisechan.ui.live2d_view import Live2DView, _normalized_gaze


class CharacterInteractionTests(unittest.TestCase):
    def test_gaze_tracks_pointer_relative_to_the_eyes(self):
        self.assertEqual(
            _normalized_gaze(750, 200, 500, 352, 1000, 800),
            (0.5, 0.38),
        )

    def test_gaze_is_clamped_when_pointer_is_beyond_screen_edges(self):
        self.assertEqual(
            _normalized_gaze(-100, 900, 500, 352, 1000, 800),
            (-1.0, -1.0),
        )

    def test_redraw_applies_smoothed_gaze_to_live2d_eye_parameters(self):
        view = Live2DView.__new__(Live2DView)
        view.failed = False
        view.shutdown_requested = False
        view.live2d = Mock()
        view.model = Mock()
        view.ready_notified = False
        view.on_ready = Mock()
        view.after_idle = Mock()
        view.eye_parameter_ranges = {
            "ParamEyeBallX": (-2.0, 2.0),
            "ParamEyeBallY": (-1.0, 1.0),
            "ParamAngleX": (-30.0, 30.0),
            "ParamAngleY": (-30.0, 30.0),
        }
        view.gaze_x = 0.0
        view.gaze_y = 0.0
        view.follow_cursor = True
        view.width = 300
        view.height = 400
        view.screen_width = 1000
        view.screen_height = 800
        view.model.GetParamValueById.side_effect = {
            "ParamAngleX": 4.0,
            "ParamAngleY": -1.0,
        }.__getitem__
        for name, result in (
            ("winfo_pointerx", 750),
            ("winfo_pointery", 200),
            ("winfo_rootx", 350),
            ("winfo_rooty", 200),
        ):
            setattr(view, name, Mock(return_value=result))

        view.redraw()

        values = {
            call.args[0]: call.args[1]
            for call in view.model.SetParamById.call_args_list
        }
        self.assertAlmostEqual(values["ParamEyeBallX"], 0.4)
        self.assertAlmostEqual(values["ParamEyeBallY"], 0.152)
        self.assertAlmostEqual(values["ParamAngleX"], 6.0)
        self.assertAlmostEqual(values["ParamAngleY"], -0.088)
        view.model.Draw.assert_called_once_with()
        view.after_idle.assert_called_once_with(view.on_ready)

    def test_disabling_cursor_follow_returns_gaze_toward_center(self):
        view = Live2DView.__new__(Live2DView)
        view.follow_cursor = False
        view.gaze_x = 0.5
        view.gaze_y = -0.5
        view.width = 300
        view.height = 400
        view.screen_width = 1000
        view.screen_height = 800
        view.eye_parameter_ranges = {
            "ParamEyeBallX": (-2.0, 2.0),
            "ParamEyeBallY": (-1.0, 1.0),
            "ParamAngleX": (-30.0, 30.0),
            "ParamAngleY": (-30.0, 30.0),
        }
        view.model = Mock()
        view.model.GetParamValueById.return_value = 0.0
        view.winfo_pointerx = Mock()
        view.winfo_pointery = Mock()

        view._update_gaze()

        self.assertAlmostEqual(view.gaze_x, 0.3)
        self.assertAlmostEqual(view.gaze_y, -0.3)
        view.winfo_pointerx.assert_not_called()
        view.winfo_pointery.assert_not_called()

    def test_character_enters_from_offscreen_right_after_loading(self):
        character = CharacterBlock.__new__(CharacterBlock)
        character._entry_started = False
        character._entry_active = False
        character._entry_after_id = None
        character.app = Mock()
        character.app.screen_width = 1920
        character.target_x = 1468
        character.target_y = 522
        character.exists = Mock(return_value=True)
        character.window = Mock()
        character.move_to = Mock()
        character._animate_entry = Mock()

        character._start_entry_animation()

        character.move_to.assert_called_once_with(1936, 522)
        character.window.attributes.assert_called_once_with("-alpha", 1.0)
        character._animate_entry.assert_called_once_with(0)

    def test_character_entry_finishes_at_initial_position_and_shows_greeting(self):
        character = CharacterBlock.__new__(CharacterBlock)
        character._entry_active = True
        character._entry_after_id = 101
        character.app = Mock()
        character.app.screen_width = 1920
        character.target_x = 1468
        character.target_y = 522
        character.exists = Mock(return_value=True)
        character.window = Mock()
        character.move_to = Mock()

        character._animate_entry(character.ENTRY_ANIMATION_DURATION_MS)

        self.assertFalse(character._entry_active)
        self.assertIsNone(character._entry_after_id)
        character.move_to.assert_called_with(1468, 522)
        character.app._character_entered.assert_called_once_with()

    def test_single_click_plays_reaction_after_double_click_window(self):
        character = CharacterBlock.__new__(CharacterBlock)
        character._dragged = False
        character._click_after_id = None
        character.window = Mock()
        character.window.after.return_value = "single-click"
        character.app = Mock()
        character.app.animate_on_click = True
        character.play_reaction = Mock(return_value=7)

        result = character._on_character_click()

        self.assertEqual(result, "break")
        character.window.after.assert_called_once_with(
            character.DOUBLE_CLICK_INTERVAL_MS,
            character._finish_single_click,
        )
        character.play_reaction.assert_not_called()
        character._finish_single_click()
        character.play_reaction.assert_called_once_with()

    def test_single_click_does_not_react_when_disabled(self):
        character = CharacterBlock.__new__(CharacterBlock)
        character._dragged = False
        character._click_after_id = None
        character.window = Mock()
        character.window.after.return_value = "single-click"
        character.app = Mock()
        character.app.animate_on_click = False
        character.play_reaction = Mock()

        character._on_character_click()
        character._finish_single_click()

        character.play_reaction.assert_not_called()

    def test_double_click_opens_menu_without_playing_single_click_motion(self):
        character = CharacterBlock.__new__(CharacterBlock)
        character._dragged = False
        character._click_after_id = None
        character.window = Mock()
        character.window.after.return_value = "single-click"
        character.app = Mock()
        character.play_reaction = Mock()

        character._on_character_click()
        result = character._on_character_click()

        self.assertEqual(result, "break")
        character.window.after_cancel.assert_called_once_with("single-click")
        character.app.toggle_controls_menu.assert_called_once_with()
        character.play_reaction.assert_not_called()
        self.assertIsNone(character._click_after_id)

    def test_composed_motion_sequence_starts_in_declared_order(self):
        view = Live2DView.__new__(Live2DView)
        view.failed = False
        view.shutdown_requested = False
        view.motion_count = 27
        view.model = Mock()
        view.live2d = SimpleNamespace(
            MotionPriority=SimpleNamespace(FORCE=2),
        )
        view.motion_durations = [0.0] * 27
        view.motion_timer_id = None
        view.motion_queue = []
        view.pending_motion_index = None
        view.pending_sequence = None
        view.after = Mock(return_value="motion-timer")

        result = view.play_sequence("greeting")

        self.assertTrue(result)
        self.assertEqual(view.motion_queue, [7])
        self.assertEqual(view.model.StartMotion.call_args.args[1], 23)

        view._finish_motion()

        self.assertEqual(view.model.StartMotion.call_count, 2)
        self.assertEqual(view.model.StartMotion.call_args.args[1], 7)

    def test_composed_motion_can_be_queued_until_live2d_loads(self):
        view = Live2DView.__new__(Live2DView)
        view.failed = False
        view.shutdown_requested = False
        view.motion_count = 0
        view.model = None
        view.motion_queue = []
        view.pending_motion_index = None
        view.pending_sequence = None

        self.assertTrue(view.play_sequence("greeting"))
        self.assertEqual(view.pending_sequence, "greeting")

    def test_dragging_character_does_not_trigger_click_motion(self):
        character = CharacterBlock.__new__(CharacterBlock)
        character._dragged = True
        character._click_after_id = None
        character.play_reaction = Mock()

        character._on_character_click()

        character.play_reaction.assert_not_called()

    def test_drag_threshold_distinguishes_click_from_movement(self):
        block = FloatingBlock.__new__(FloatingBlock)
        block.window = Mock()
        block.window.winfo_x.return_value = 10
        block.window.winfo_y.return_value = 20
        block.move_to = Mock()
        block._start_drag(SimpleNamespace(x_root=15, y_root=25))

        block._drag(SimpleNamespace(x_root=18, y_root=28))
        self.assertFalse(block._dragged)

        block._drag(SimpleNamespace(x_root=20, y_root=25))
        self.assertTrue(block._dragged)


if __name__ == "__main__":
    unittest.main()

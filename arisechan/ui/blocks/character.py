import tkinter as tk
from pathlib import Path

from arisechan.ui.live2d_view import LIVE2D_TRANSPARENT, Live2DView
from .base import FloatingBlock
from .constants import CHARACTER_HEIGHT, CHARACTER_WIDTH

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CharacterBlock(FloatingBlock):
    ENTRY_ANIMATION_DURATION_MS = 850
    ENTRY_ANIMATION_INTERVAL_MS = 16
    ENTRY_OFFSCREEN_MARGIN = 16
    DOUBLE_CLICK_INTERVAL_MS = 500

    def __init__(self, app, x, y, on_close):
        self.image = None
        self.image_label = None
        self.target_x = x
        self.target_y = y
        self._entry_started = False
        self._entry_active = False
        self._entry_after_id = None
        self._click_after_id = None

        super().__init__(
            app,
            x,
            y,
            CHARACTER_WIDTH,
            CHARACTER_HEIGHT,
            background=LIVE2D_TRANSPARENT,
            transparent=True,
            transparent_color=LIVE2D_TRANSPARENT,
            on_close=on_close,
        )
        self.window.attributes("-alpha", 0.0)
        model_path = (
            PROJECT_ROOT
            / "assets"
            / "live2d"
            / "haru_greeter_t05"
            / "runtime"
            / "haru_greeter_t05.model3.json"
        )
        self.live2d_view = Live2DView(
            self.window,
            model_path,
            self._live2d_failed,
            CHARACTER_WIDTH,
            CHARACTER_HEIGHT,
            on_ready=self._live2d_ready,
        )
        self.live2d_view.set_follow_cursor(
            getattr(self.app, "follow_cursor", True)
        )
        self.live2d_view.place(
            x=0,
            y=0,
            width=CHARACTER_WIDTH,
            height=CHARACTER_HEIGHT,
        )
        for widget in (self.live2d_view,):
            self.bind_drag(widget, button=1)
            self.bind_drag(widget, button=3)
            widget.bind("<ButtonRelease-1>", self._on_character_click)
        self.add_close_button("#fffdfd", y=6)

    def _live2d_ready(self):
        self._start_entry_animation()

    def _start_entry_animation(self):
        if self._entry_started or not self.exists():
            return

        self._entry_started = True
        self._entry_active = True
        self.move_to(
            self.app.screen_width + self.ENTRY_OFFSCREEN_MARGIN,
            self.target_y,
        )
        self.window.attributes("-alpha", 1.0)
        self._animate_entry(0)

    def _animate_entry(self, elapsed_ms):
        if not self._entry_active or not self.exists():
            return

        progress = min(1.0, elapsed_ms / self.ENTRY_ANIMATION_DURATION_MS)
        eased_progress = 1 - (1 - progress) ** 3
        start_x = self.app.screen_width + self.ENTRY_OFFSCREEN_MARGIN
        x = round(start_x + (self.target_x - start_x) * eased_progress)
        self.move_to(x, self.target_y)

        if progress < 1:
            self._entry_after_id = self.window.after(
                self.ENTRY_ANIMATION_INTERVAL_MS,
                self._animate_entry,
                elapsed_ms + self.ENTRY_ANIMATION_INTERVAL_MS,
            )
            return

        self._entry_active = False
        self._entry_after_id = None
        self.move_to(self.target_x, self.target_y)
        self.app._character_entered()

    def _drag(self, event):
        if self._entry_after_id is not None:
            self.window.after_cancel(self._entry_after_id)
            self._entry_after_id = None
            self._entry_active = False
            self.app._character_entered()
        super()._drag(event)
        self.app._character_moved()

    def _on_character_click(self, _event=None):
        if getattr(self, "_dragged", False):
            self._cancel_pending_click()
            return "break"

        if self._click_after_id is not None:
            self._cancel_pending_click()
            self.app.toggle_controls_menu()
            return "break"

        self._click_after_id = self.window.after(
            self.DOUBLE_CLICK_INTERVAL_MS,
            self._finish_single_click,
        )
        return "break"

    def _finish_single_click(self):
        self._click_after_id = None
        if getattr(self.app, "animate_on_click", True):
            self.play_reaction()

    def _cancel_pending_click(self):
        if self._click_after_id is not None:
            self.window.after_cancel(self._click_after_id)
            self._click_after_id = None

    def _live2d_failed(self, error):
        if not self.exists():
            return

        if self.live2d_view is not None:
            self.live2d_view.shutdown()
            self.live2d_view.destroy()
            self.live2d_view = None
        self._show_png_fallback()
        self.image_label.lift()
        self._start_entry_animation()
        self.app._live2d_error(error)

    def _show_png_fallback(self):
        if self.image_label is not None:
            return

        from PIL import Image, ImageTk

        image_path = PROJECT_ROOT / "assets" / "character.png"
        if not image_path.is_file():
            raise FileNotFoundError(f"Character image not found: {image_path}")

        with Image.open(image_path) as source:
            image = source.convert("RGBA")
            image.thumbnail(
                (CHARACTER_WIDTH, CHARACTER_HEIGHT),
                Image.Resampling.LANCZOS,
            )
        self.image = ImageTk.PhotoImage(image, master=self.app.root)
        self.image_label = tk.Label(
            self.window,
            image=self.image,
            bg=LIVE2D_TRANSPARENT,
            anchor="s",
            borderwidth=0,
            highlightthickness=0,
            cursor="fleur",
        )
        self.image_label.place(
            x=0,
            y=0,
            width=CHARACTER_WIDTH,
            height=CHARACTER_HEIGHT,
        )
        self.bind_drag(self.image_label, button=1)
        self.bind_drag(self.image_label, button=3)
        self.image_label.bind("<ButtonRelease-1>", self._on_character_click)

    def play_reaction(self):
        if self.live2d_view is not None:
            return self.live2d_view.play_reaction()
        return None

    def set_follow_cursor(self, enabled):
        if self.live2d_view is not None:
            self.live2d_view.set_follow_cursor(enabled)

    def play_motion(self, motion_index):
        return bool(
            self.live2d_view
            and self.live2d_view.play_motion(motion_index)
        )

    def play_sequence(self, sequence_name):
        return bool(
            self.live2d_view
            and self.live2d_view.play_sequence(sequence_name)
        )

    def return_to_idle(self):
        return bool(
            self.live2d_view
            and self.live2d_view.return_to_idle()
        )

    def close(self, notify=True):
        self._cancel_pending_click()
        if self._entry_after_id is not None:
            self.window.after_cancel(self._entry_after_id)
            self._entry_after_id = None
            self._entry_active = False
        if self.live2d_view is not None:
            self.live2d_view.shutdown()
        super().close(notify=notify)

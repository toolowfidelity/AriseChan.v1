import tkinter as tk

from .base import FloatingBlock


class ControlsBlock(FloatingBlock):
    WIDTH = 206
    HEIGHT = 178
    GAP = 12

    def __init__(self, app, x, y, on_close):
        super().__init__(
            app,
            x,
            y,
            self.WIDTH,
            self.HEIGHT,
            background="#171522",
            on_close=on_close,
        )
        self.frame = tk.Frame(
            self.window,
            bg="#171522",
            highlightbackground="#51465f",
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        self.frame.pack(fill="both", expand=True)
        tk.Label(
            self.frame,
            text="Arise",
            bg="#171522",
            fg="#f4efff",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 7))
        self.settings_button = self._add_button(
            "⚙  Настройки",
            app.open_settings,
        )
        self.visibility_button = self._add_button(
            "◉  Скрыть персонажа",
            app.toggle_character,
        )
        self._add_button("⏻  Выход", app.shutdown)
        self.status_label = tk.Label(
            self.frame,
            text=app.idle_status(),
            bg="#171522",
            fg="#aaa2bd",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(7, 0))
        self.bind_drag(self.frame)
        self.add_close_button("#171522")

    def _add_button(self, text, command):
        button = tk.Button(
            self.frame,
            text=text,
            command=command,
            bg="#2c2740",
            fg="#f4efff",
            activebackground="#403750",
            activeforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9),
            cursor="hand2",
            anchor="w",
            padx=9,
            pady=5,
        )
        button.pack(fill="x", pady=2)
        return button

    def set_character_visible(self, visible):
        if self.exists():
            self.visibility_button.config(
                text="◉  Скрыть персонажа"
                if visible
                else "◉  Показать персонажа"
            )

    def set_status(self, text):
        if self.exists():
            self.status_label.config(text=text)

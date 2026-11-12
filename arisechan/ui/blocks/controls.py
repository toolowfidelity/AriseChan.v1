import tkinter as tk

from .base import FloatingBlock


class ControlsBlock(FloatingBlock):
    def __init__(self, app, x, y, on_close):
        super().__init__(
            app,
            x,
            y,
            188,
            48,
            background="#fffdfd",
            on_close=on_close,
        )
        self.frame = tk.Frame(
            self.window,
            bg="#fffdfd",
            highlightbackground="#d9d1df",
            highlightthickness=1,
            padx=5,
            pady=4,
        )
        self.frame.pack(fill="both", expand=True)
        tk.Button(
            self.frame,
            text="⚙",
            command=app.open_settings,
            bg="#fffdfd",
            fg="#655a6d",
            activebackground="#eee8f2",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 11),
            cursor="hand2",
            padx=5,
        ).pack(side="left")
        tk.Button(
            self.frame,
            text="◉",
            command=app.toggle_character,
            bg="#fffdfd",
            fg="#655a6d",
            activebackground="#eee8f2",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=5,
        ).pack(side="left")
        self.status_label = tk.Label(
            self.frame,
            text=app.idle_status(),
            bg="#fffdfd",
            fg="#766c7c",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=(3, 17))
        self.bind_drag(self.frame)
        self.add_close_button("#fffdfd")

    def set_status(self, text):
        if self.exists():
            self.status_label.config(text=text)

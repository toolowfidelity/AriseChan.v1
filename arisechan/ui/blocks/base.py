import tkinter as tk

from .constants import TRANSPARENT


class FloatingBlock:
    def __init__(
        self,
        app,
        x,
        y,
        width,
        height,
        background,
        transparent=False,
        transparent_color=TRANSPARENT,
        on_close=None,
    ):
        self.app = app
        self.x = int(x)
        self.y = int(y)
        self.width = width
        self.height = height
        self.on_close = on_close
        self.transparent_color = transparent_color
        self.window = tk.Toplevel(app.root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=transparent_color if transparent else background)
        if transparent:
            self.window.attributes("-transparentcolor", transparent_color)
        self.window.geometry(f"{width}x{height}+{self.x}+{self.y}")
        self.close_button = None

    def add_close_button(
        self,
        background,
        x=None,
        y=1,
        foreground="#68636d",
        active_foreground="#514d56",
    ):
        self.close_button = tk.Button(
            self.window,
            text="×",
            bg=background,
            fg=foreground,
            activebackground=background,
            activeforeground=active_foreground,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            takefocus=False,
            command=self.close,
        )
        self.close_button.place(
            x=self.width - 22 if x is None else x,
            y=y,
            width=20,
            height=20,
        )
        self.close_button.lift()

    def bind_drag(self, widget, button=3):
        widget.bind(f"<ButtonPress-{button}>", self._start_drag)
        widget.bind(f"<B{button}-Motion>", self._drag)

    def _start_drag(self, event):
        self._drag_offset = (
            event.x_root - self.window.winfo_x(),
            event.y_root - self.window.winfo_y(),
        )
        self._drag_origin = (event.x_root, event.y_root)
        self._dragged = False

    def _drag(self, event):
        if max(
            abs(event.x_root - self._drag_origin[0]),
            abs(event.y_root - self._drag_origin[1]),
        ) > 4:
            self._dragged = True
        self.move_to(
            event.x_root - self._drag_offset[0],
            event.y_root - self._drag_offset[1],
        )

    def move_to(self, x, y):
        self.x = int(x)
        self.y = int(y)
        self.window.geometry(f"+{self.x}+{self.y}")

    def position(self):
        self.window.update_idletasks()
        self.x = self.window.winfo_x()
        self.y = self.window.winfo_y()
        return self.x, self.y

    def exists(self):
        return bool(self.window.winfo_exists())

    def close(self, notify=True):
        if self.exists():
            self.window.destroy()
        if notify and self.on_close:
            self.on_close(self)

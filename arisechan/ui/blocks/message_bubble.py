import tkinter as tk

from .base import FloatingBlock
from .constants import (
    BUBBLE_COLORS,
    BUBBLE_INPUT_HEIGHT,
    BUBBLE_OUTLINE,
    COMPOSER_ACCENT,
    COMPOSER_BACKGROUND,
    COMPOSER_FOREGROUND,
    TRANSPARENT,
)


class MessageBubbleBlock(FloatingBlock):
    def __init__(
        self,
        app,
        role,
        content,
        lines,
        x,
        y,
        width,
        height,
        on_close,
        tail_extension=0,
    ):
        self.background, self.foreground = BUBBLE_COLORS.get(
            role,
            BUBBLE_COLORS["assistant"],
        )
        self.bubble_width = width
        self.message_height = height
        self.tail_extension = tail_extension
        self.body_left = 2
        self.body_right = width - 25
        self.input_visible = False
        self.input_frame = None
        window_width = width + tail_extension
        super().__init__(
            app,
            x,
            y,
            window_width,
            height,
            background=TRANSPARENT,
            transparent=True,
            on_close=on_close,
        )
        self.role = role
        self.content = content
        self.lines = lines
        self.canvas = tk.Canvas(
            self.window,
            width=window_width,
            height=height,
            bg=TRANSPARENT,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_bubble()
        self.canvas.bind(
            "<Button-1>",
            lambda _event: app.open_composer(self),
        )
        self.bind_drag(self.canvas)
        self.add_close_button(
            self.background,
            x=self.body_right - 20,
            y=0,
            foreground="#d0c6d6",
            active_foreground="#ffffff",
        )

    def show_composer(self):
        if self.input_visible:
            self.entry.focus_set()
            return

        self.input_visible = True
        self.height = self.message_height + BUBBLE_INPUT_HEIGHT
        self.window.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.canvas.configure(height=self.height)
        self._draw_bubble()
        self.entry.focus_set()

    def hide_composer(self):
        if not self.input_visible:
            return

        self.input_visible = False
        self.input_frame.destroy()
        self.input_frame = None
        self.height = self.message_height
        self.window.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.canvas.configure(height=self.height)
        self._draw_bubble()

    def update_content(self, content, lines, height):
        self.content = content
        self.lines = lines
        self.message_height = height
        self.height = height + (BUBBLE_INPUT_HEIGHT if self.input_visible else 0)
        self.window.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.canvas.configure(height=self.height)
        self._draw_bubble()

    def _draw_bubble(self):
        self.canvas.delete("all")
        self.canvas.configure(width=self.width, height=self.height)
        outline = BUBBLE_OUTLINE
        body_left = self.body_left
        body_right = self.body_right
        body_top = 2
        body_bottom = self.height - 2
        radius = 24
        center_y = self.message_height // 2
        tail_top = center_y - 10
        tail_bottom = center_y + 10
        tail_tip = self.width - 1
        tail_base = body_right
        tail_points = (
            (tail_base, tail_top),
            (tail_tip, center_y),
            (tail_base, tail_bottom),
        )
        self.canvas.create_polygon(
            *[value for point in tail_points for value in point],
            fill=self.background,
            outline="",
            tags=("bubble_tail",),
        )

        self.canvas.create_rectangle(
            body_left + radius,
            body_top,
            body_right - radius,
            body_bottom,
            fill=self.background,
            outline="",
            tags=("bubble_body_fill",),
        )
        self.canvas.create_rectangle(
            body_left,
            body_top + radius,
            body_right,
            body_bottom - radius,
            fill=self.background,
            outline="",
            tags=("bubble_body_fill",),
        )
        for left, top in (
            (body_left, body_top),
            (body_right - radius * 2, body_top),
            (body_left, body_bottom - radius * 2),
            (body_right - radius * 2, body_bottom - radius * 2),
        ):
            self.canvas.create_oval(
                left,
                top,
                left + radius * 2,
                top + radius * 2,
                fill=self.background,
                outline="",
                tags=("bubble_body_fill",),
            )

        arc_boxes = (
            (body_left, body_top, body_left + radius * 2, body_top + radius * 2, 90),
            (body_right - radius * 2, body_top, body_right, body_top + radius * 2, 0),
            (body_right - radius * 2, body_bottom - radius * 2, body_right, body_bottom, 270),
            (body_left, body_bottom - radius * 2, body_left + radius * 2, body_bottom, 180),
        )
        for x1, y1, x2, y2, start in arc_boxes:
            self.canvas.create_arc(
                x1,
                y1,
                x2,
                y2,
                start=start,
                extent=90,
                style=tk.ARC,
                outline=outline,
                width=2,
                tags=("bubble_body_outline",),
            )

        self.canvas.create_line(
            body_left + radius,
            body_top,
            body_right - radius,
            body_top,
            fill=outline,
            width=2,
            tags=("bubble_body_outline",),
        )
        self.canvas.create_line(
            body_left + radius,
            body_bottom,
            body_right - radius,
            body_bottom,
            fill=outline,
            width=2,
            tags=("bubble_body_outline",),
        )
        for side_x, side_y1, side_y2 in (
            (body_left, body_top + radius, body_bottom - radius),
            (body_right, body_top + radius, body_bottom - radius),
        ):
            if side_x == tail_base:
                self.canvas.create_line(
                    side_x,
                    side_y1,
                    side_x,
                    tail_top,
                    fill=outline,
                    width=2,
                    tags=("bubble_body_outline",),
                )
                self.canvas.create_line(
                    side_x,
                    tail_bottom,
                    side_x,
                    side_y2,
                    fill=outline,
                    width=2,
                    tags=("bubble_body_outline",),
                )
            else:
                self.canvas.create_line(
                    side_x,
                    side_y1,
                    side_x,
                    side_y2,
                    fill=outline,
                    width=2,
                    tags=("bubble_body_outline",),
                )
        self.canvas.create_line(
            tail_base,
            tail_top,
            tail_tip,
            center_y,
            fill=outline,
            width=2,
            capstyle=tk.ROUND,
            tags=("bubble_tail_outline",),
        )
        self.canvas.create_line(
            tail_base,
            tail_bottom,
            tail_tip,
            center_y,
            fill=outline,
            width=2,
            capstyle=tk.ROUND,
            tags=("bubble_tail_outline",),
        )

        centered_text = self.role == "welcome"
        self.canvas.create_text(
            (body_left + body_right) // 2 if centered_text else body_left + 24,
            center_y,
            text="\n".join(self.lines),
            width=body_right - body_left - 48,
            anchor="center" if centered_text else "w",
            justify="center" if centered_text else "left",
            fill=self.foreground,
            font=self.app.message_font,
            tags=("bubble_text",),
        )
        if self.input_visible:
            self.canvas.create_line(
                body_left + 16,
                self.message_height + 2,
                body_right - 16,
                self.message_height + 2,
                fill=outline,
                width=1,
            )
            self._draw_input()

        if self.close_button:
            self.close_button.place_configure(
                x=body_right - 20,
                y=0,
                width=20,
                height=20,
            )
            self.close_button.lift()

    def _draw_input(self):
        self.input_frame = tk.Frame(
            self.canvas,
            bg=COMPOSER_BACKGROUND,
            highlightbackground="#675a70",
            highlightthickness=1,
        )
        self.input_frame.place(
            x=self.body_left + 12,
            y=self.message_height + 10,
            width=self.body_right - self.body_left - 24,
            height=42,
        )
        self.entry = tk.Entry(
            self.input_frame,
            bg=COMPOSER_BACKGROUND,
            fg=COMPOSER_FOREGROUND,
            insertbackground=COMPOSER_FOREGROUND,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(6, 2), pady=4)
        self.entry.bind(
            "<Return>",
            lambda _event: self.app.submit_message(self.entry.get()),
        )
        tk.Button(
            self.input_frame,
            text="➤",
            command=lambda: self.app.submit_message(self.entry.get()),
            bg=COMPOSER_ACCENT,
            fg="#2d2431",
            activebackground="#d8a6ca",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=7,
        ).pack(side="right", fill="y", padx=4, pady=4)

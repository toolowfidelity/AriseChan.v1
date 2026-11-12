import ctypes
import queue
import sys
import threading
import tkinter as tk
from ctypes import wintypes
from tkinter import font as tkfont
from tkinter import messagebox

from arisechan.services.openai_client import MODEL, OpenAIClient, OpenAIError
from arisechan.services.communication_style import build_system_prompt
from arisechan.services.ollama_client import (
    DEFAULT_MODEL as OLLAMA_MODEL,
    OllamaClient,
    OllamaError,
    num_predict_for_conciseness,
)
from arisechan.services.offline_responder import (
    reply_to,
    reply_to_motion,
    reply_to_sequence,
)
from arisechan.services.motion_commands import (
    MOTION_COUNT,
    MotionCommand,
    format_motion_list,
    parse_motion_command,
)
from arisechan.storage.credential_store import (
    CredentialStoreError,
    load_api_key,
)
from arisechan.storage.settings_store import SettingsError, load_preferences
from arisechan.ui.bubble_layout import (
    BUBBLE_GAP,
    BUBBLE_TAIL_EXTENSION,
    BUBBLE_TEXT_WIDTH,
    BUBBLE_WIDTH,
    bubble_height,
    find_bubble_position,
    wrap_text,
)
from arisechan.ui.blocks import (
    CHARACTER_HEIGHT,
    CHARACTER_WIDTH,
    CHARACTER_RIGHT_MARGIN,
    CHARACTER_TASKBAR_OVERLAP,
    CharacterBlock,
    ControlsBlock,
    MessageBubbleBlock,
)
from arisechan.ui.settings_dialog import open_settings_dialog


SPI_GETWORKAREA = 0x0030
MAX_CHAT_HISTORY = 40
MAX_API_CONTEXT_MESSAGES = 20
MAX_OLLAMA_CONTEXT_MESSAGES = 8


def _taskbar_top(screen_height):
    if sys.platform != "win32":
        return screen_height

    work_area = wintypes.RECT()
    succeeded = ctypes.windll.user32.SystemParametersInfoW(
        SPI_GETWORKAREA,
        0,
        ctypes.byref(work_area),
        0,
    )
    return work_area.bottom if succeeded else screen_height


class AriseOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AriseChan")
        try:
            self.preferences = load_preferences()
            self.persona = self.preferences["persona"]
            self.api_key_configured = load_api_key() is not None
        except (CredentialStoreError, SettingsError) as error:
            messagebox.showerror("Настройки Arise", str(error), parent=self.root)
            self.root.destroy()
            raise
        self.root.withdraw()

        self.follow_cursor = self.preferences["follow_cursor"]
        self.animate_on_click = self.preferences["animate_on_click"]
        self.greet_on_start = self.preferences["greet_on_start"]
        self.ai_provider = self.preferences["ai_provider"]
        self.ollama_model = self.preferences.get("ollama_model", OLLAMA_MODEL)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.taskbar_top = _taskbar_top(self.screen_height)
        self.message_font = tkfont.Font(
            root=self.root,
            family="Segoe UI",
            size=10,
        )
        self.history = []
        self.pending_turn_bubble = None
        self.responses = queue.Queue()
        self.is_responding = False
        self.message_blocks = []
        self.composer_anchor = None
        self.welcome_shown = False

        self.character_block = self._create_character()
        self.controls_block = None

        self.root.bind_all("<Escape>", lambda _event: self.shutdown())
        self.root.bind_all("<Control-Shift-a>", self._restore_controls)
        self.root.after(100, self._poll_responses)

    def shutdown(self):
        if self.character_block and self.character_block.exists():
            self.character_block.close(notify=False)
        self.root.destroy()

    def idle_status(self):
        if self.ai_provider == "ollama":
            return f"Ollama · {self.ollama_model}"
        return f"OpenAI · {MODEL}" if self.api_key_configured else "Локальный режим"

    def _default_character_position(self):
        return (
            max(12, self.screen_width - CHARACTER_WIDTH - CHARACTER_RIGHT_MARGIN),
            max(
                8,
                self.taskbar_top - CHARACTER_HEIGHT + CHARACTER_TASKBAR_OVERLAP,
            ),
        )

    def _create_character(self):
        x, y = self._default_character_position()
        return CharacterBlock(self, x, y, self._character_closed)

    def _create_controls(self):
        char_x, char_y = (
            self.character_block.position()
            if self.character_block and self.character_block.exists()
            else self._default_character_position()
        )
        x, y = self._controls_position(char_x, char_y)
        return ControlsBlock(self, x, y, self._controls_closed)

    def _controls_position(self, char_x, char_y):
        if char_x + CHARACTER_WIDTH // 2 >= self.screen_width // 2:
            x = char_x - ControlsBlock.WIDTH - ControlsBlock.GAP
        else:
            x = char_x + CHARACTER_WIDTH + ControlsBlock.GAP
        max_x = max(8, self.screen_width - ControlsBlock.WIDTH - 8)
        x = max(8, min(max_x, x))
        y = char_y + (CHARACTER_HEIGHT - ControlsBlock.HEIGHT) // 2
        max_y = max(
            8,
            getattr(self, "taskbar_top", self.screen_height)
            - ControlsBlock.HEIGHT,
        )
        y = max(8, min(max_y, y))
        return x, y

    def _controls_closed(self, block):
        if self.controls_block is block:
            self.controls_block = None
        self._maybe_shutdown()

    def _character_closed(self, block):
        if self.character_block is block:
            self.character_block = None
        if self.controls_block and self.controls_block.exists():
            self.controls_block.set_character_visible(False)
        self._maybe_shutdown()

    def _bubble_closed(self, block):
        if block in self.message_blocks:
            self.message_blocks.remove(block)
        if self.composer_anchor is block:
            self.composer_anchor = None
        self._layout_message_stack()
        self._maybe_shutdown()

    def _maybe_shutdown(self):
        if (
            self.character_block is None
            and self.controls_block is None
            and not self.message_blocks
        ):
            self.shutdown()

    def _restore_controls(self, _event=None):
        if self.character_block is None:
            self.character_block = self._create_character()
        if self.controls_block is None:
            self.controls_block = self._create_controls()
        return "break"

    def toggle_controls_menu(self):
        if self.controls_block and self.controls_block.exists():
            self.controls_block.close()
        else:
            self.controls_block = self._create_controls()

    def toggle_character(self):
        if self.character_block and self.character_block.exists():
            self.character_block.close()
        else:
            self.character_block = self._create_character()
        if self.controls_block and self.controls_block.exists():
            self.controls_block.set_character_visible(
                bool(self.character_block and self.character_block.exists())
            )

    def _character_moved(self):
        if not self.character_block or not self.character_block.exists():
            return

        char_x, char_y = self.character_block.position()
        if self.controls_block and self.controls_block.exists():
            self.controls_block.move_to(*self._controls_position(char_x, char_y))

        self._layout_message_stack()

    def _character_entered(self):
        self._character_moved()
        if self.character_block and self.greet_on_start:
            self.character_block.play_sequence("greeting")
        if self.welcome_shown:
            return
        self.welcome_shown = True
        self._spawn_message_block(
            "welcome",
            "Привет! Я Arise. Нажми на облачко, чтобы написать мне.",
            animate=False,
        )

    def close_composer(self):
        if self.composer_anchor:
            bubble = self.composer_anchor
            self.composer_anchor = None
            bubble.hide_composer()

    def open_composer(self, bubble):
        if self.composer_anchor and self.composer_anchor is not bubble:
            self.composer_anchor.hide_composer()
        self.composer_anchor = bubble
        bubble.show_composer()

    def _layout_message_stack(self):
        if not self.message_blocks:
            return

        newest = self.message_blocks[-1]
        _, current_y = find_bubble_position(
            newest.width,
            newest.message_height,
            self.character_block,
            self.screen_width,
            self.screen_height,
            getattr(self, "taskbar_top", self.screen_height),
        )
        visible_blocks = []
        for bubble in reversed(self.message_blocks):
            x, _ = find_bubble_position(
                bubble.width,
                bubble.message_height,
                self.character_block,
                self.screen_width,
                self.screen_height,
                getattr(self, "taskbar_top", self.screen_height),
            )
            if bubble is not newest:
                current_y -= bubble.message_height + BUBBLE_GAP
            if current_y < 8:
                if bubble is self.composer_anchor:
                    self.close_composer()
                bubble.close(notify=False)
                continue
            bubble.move_to(x, current_y)
            visible_blocks.append(bubble)

        self.message_blocks = list(reversed(visible_blocks))

    def _spawn_message_block(self, role, content, animate=True):
        if self.composer_anchor:
            self.close_composer()

        lines = wrap_text(content, self.message_font, BUBBLE_TEXT_WIDTH)
        height = bubble_height(lines, self.message_font)
        tail_extension = (
            BUBBLE_TAIL_EXTENSION
            if self.character_block and self.character_block.exists()
            else 0
        )
        bubble_width = BUBBLE_WIDTH + tail_extension
        x, y = find_bubble_position(
            bubble_width,
            height,
            self.character_block,
            self.screen_width,
            self.screen_height,
            getattr(self, "taskbar_top", self.screen_height),
        )
        block = MessageBubbleBlock(
            self,
            role,
            content,
            lines,
            x,
            y,
            BUBBLE_WIDTH,
            height,
            self._bubble_closed,
            tail_extension=tail_extension,
        )
        self.message_blocks.append(block)
        self._layout_message_stack()
        if (
            animate
            and role in {"assistant", "welcome"}
            and self.character_block
        ):
            self.character_block.play_reaction()
        return block

    def _record_message(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_CHAT_HISTORY:
            del self.history[:-MAX_CHAT_HISTORY]

    def _start_turn_bubble(self, message):
        if self.composer_anchor:
            self.close_composer()
        return self._spawn_message_block(
            "assistant",
            f"Ты: {message}",
            animate=False,
        )

    def _update_turn_bubble(self, bubble, message, response, animate=True):
        content = f"Ты: {message}\n\nАриша: {response}"
        if bubble and bubble.exists():
            lines = wrap_text(content, self.message_font, BUBBLE_TEXT_WIDTH)
            bubble.update_content(
                content,
                lines,
                bubble_height(lines, self.message_font),
            )
            self._layout_message_stack()
        else:
            bubble = self._spawn_message_block("assistant", content, animate=False)

        if animate and self.character_block:
            self.character_block.play_reaction()
        return bubble

    def _live2d_error(self, error):
        self._set_status("Live2D error · PNG fallback")
        messagebox.showerror(
            "Live2D не запущен",
            (
                "Не удалось загрузить модель Haru. Сейчас показана запасная "
                f"картинка персонажа.\n\n{error}"
            ),
            parent=self._dialog_parent(),
        )

    def submit_message(self, content):
        message = content.strip()
        if not message or self.is_responding:
            return

        motion_command = parse_motion_command(message)
        if motion_command:
            self._handle_motion_command(message, motion_command)
            return

        if self.ai_provider == "ollama":
            self._start_ollama_response(message)
            return

        try:
            api_key = load_api_key()
        except CredentialStoreError as error:
            self.api_key_configured = False
            self._start_local_response(message, f"Не удалось прочитать ключ OpenAI: {error}")
            return

        if not api_key:
            self.api_key_configured = False
            self._start_local_response(message)
            return

        self.api_key_configured = True
        turn_bubble = self._start_turn_bubble(message)
        self._record_message("user", message)
        self.is_responding = True
        self._set_status("Отправляю...")
        request_messages = self._request_messages()
        self.pending_turn_bubble = turn_bubble
        threading.Thread(
            target=self._request_response,
            args=(api_key, request_messages, message),
            daemon=True,
        ).start()

    def _start_ollama_response(self, message):
        turn_bubble = self._start_turn_bubble(message)
        self._record_message("user", message)
        self.is_responding = True
        self._set_status("Ollama · отвечает...")
        request_messages = self._request_messages(MAX_OLLAMA_CONTEXT_MESSAGES)
        conciseness = self.preferences["communication_style"]["conciseness"]
        num_predict = num_predict_for_conciseness(conciseness)
        self.pending_turn_bubble = turn_bubble
        threading.Thread(
            target=self._request_ollama_response,
            args=(self.ollama_model, request_messages, message, num_predict),
            daemon=True,
        ).start()

    def _request_ollama_response(self, model, messages, user_message, num_predict):
        try:
            answer = OllamaClient(model, num_predict=num_predict).reply(messages)
        except OllamaError as error:
            self.responses.put((None, str(error), user_message))
        else:
            self.responses.put((answer, None, user_message))

    def _handle_motion_command(self, message, command: MotionCommand):
        turn_bubble = self._start_turn_bubble(message)
        self._record_message("user", message)

        if command.action == "sequence":
            if (
                command.sequence is None
                or not self.character_block
                or not self.character_block.play_sequence(command.sequence)
            ):
                response = (
                    "Не получилось запустить анимацию: персонаж скрыт или "
                    "Live2D ещё загружается."
                )
                status = "Live2D недоступен"
            else:
                response = reply_to_sequence(command.sequence)
                status = f"Live2D · {command.sequence}"
        elif command.action == "list":
            response = format_motion_list()
            status = self.idle_status()
        elif command.action == "idle":
            if self.character_block and self.character_block.return_to_idle():
                response = "Остановила движение и вернулась в режим ожидания."
                status = "Live2D · ожидание"
            else:
                response = "Сейчас персонаж скрыт или Live2D-модель не загружена."
                status = "Live2D недоступен"
        elif command.action == "random":
            motion_index = (
                self.character_block.play_reaction()
                if self.character_block
                else None
            )
            if motion_index is None:
                response = (
                    "Не получилось запустить движение: персонаж скрыт или "
                    "Live2D ещё загружается."
                )
                status = "Live2D недоступен"
            else:
                response = reply_to_motion(motion_index, randomly_selected=True)
                status = f"Live2D · движение {motion_index:02d}"
        else:
            motion_index = command.number
            if motion_index is None or not 1 <= motion_index <= MOTION_COUNT:
                response = (
                    f"Номер должен быть от 1 до {MOTION_COUNT}. "
                    "Напиши «список движений», чтобы увидеть варианты."
                )
                status = "Live2D · неверный номер"
            elif not self.character_block or not self.character_block.play_motion(
                motion_index
            ):
                response = (
                    "Не получилось запустить движение: персонаж скрыт или "
                    "Live2D ещё загружается."
                )
                status = "Live2D недоступен"
            else:
                response = reply_to_motion(motion_index)
                status = f"Live2D · движение {motion_index:02d}"

        self._record_message("assistant", response)
        self._update_turn_bubble(
            turn_bubble,
            message,
            response,
            animate=False,
        )
        self._set_status(status)

    def _start_local_response(self, message, notice=None):
        turn_bubble = self._start_turn_bubble(message)
        self._record_message("user", message)
        self.is_responding = True
        self._set_status("Локальный режим")
        response = reply_to(message)
        if notice:
            response = f"{notice}\n\n{response}"
        self.root.after(
            320,
            self._finish_local_response,
            message,
            response,
            turn_bubble,
        )

    def _finish_local_response(self, message, response, turn_bubble):
        self._record_message("assistant", response)
        self._update_turn_bubble(turn_bubble, message, response)
        self.is_responding = False
        self._set_status("Локальный режим")

    def open_settings(self, prompted_by_send=False):
        open_settings_dialog(
            self._dialog_parent(),
            self.persona,
            self.preferences,
            self._settings_saved,
            prompted_by_send=prompted_by_send,
        )

    def _settings_saved(self, persona, api_key_configured, preferences):
        self.persona = persona
        self.api_key_configured = api_key_configured
        self.preferences.update(preferences)
        self.preferences["persona"] = persona
        self.ai_provider = preferences["ai_provider"]
        self.ollama_model = preferences["ollama_model"]
        self.follow_cursor = preferences["follow_cursor"]
        self.animate_on_click = preferences["animate_on_click"]
        self.greet_on_start = preferences["greet_on_start"]
        if self.character_block:
            self.character_block.set_follow_cursor(self.follow_cursor)
        self._set_status(self.idle_status())

    def _dialog_parent(self):
        if self.controls_block and self.controls_block.exists():
            return self.controls_block.window
        if self.character_block and self.character_block.exists():
            return self.character_block.window
        return self.root

    def _set_status(self, text):
        if self.controls_block and self.controls_block.exists():
            self.controls_block.set_status(text)

    def _request_messages(self, max_messages=MAX_API_CONTEXT_MESSAGES):
        return [
            {
                "role": "system",
                "content": build_system_prompt(
                    self.persona,
                    self.preferences["communication_style"],
                ),
            },
            *self.history[-max_messages:],
        ]

    def _request_response(self, api_key, messages, user_message):
        try:
            answer = OpenAIClient(api_key).reply(messages)
        except OpenAIError as error:
            self.responses.put((None, str(error), user_message))
        else:
            self.responses.put((answer, None, user_message))

    def _poll_responses(self):
        while True:
            try:
                answer, error, user_message = self.responses.get_nowait()
            except queue.Empty:
                break
            self._finish_response(answer, error, user_message)
        self.root.after(100, self._poll_responses)

    def _finish_response(self, answer, error, user_message):
        self.is_responding = False
        turn_bubble = self.pending_turn_bubble
        self.pending_turn_bubble = None
        if error:
            provider = "Ollama" if self.ai_provider == "ollama" else "OpenAI"
            response = (
                f"Запрос к {provider} не выполнен: {error}\n\n"
                f"Пока отвечаю локально:\n\n{reply_to(user_message)}"
            )
            self._record_message("assistant", response)
            self._update_turn_bubble(turn_bubble, user_message, response)
            self._set_status(f"Локальный режим · ошибка {provider}")
        else:
            self._record_message("assistant", answer)
            self._update_turn_bubble(turn_bubble, user_message, answer)
            self._set_status(self.idle_status())

    def run(self):
        self.root.mainloop()

import tkinter as tk
from tkinter import messagebox, ttk

from arisechan.storage.credential_store import (
    CredentialStoreError,
    delete_api_key,
    load_api_key,
    save_api_key,
)
from arisechan.storage.settings_store import SettingsError, save_preferences


class ScrollableTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#171522")
        self.canvas = tk.Canvas(
            self,
            bg="#171522",
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            bg="#2c2740",
            activebackground="#e9a6d7",
            troughcolor="#171522",
            highlightthickness=0,
            borderwidth=0,
            width=12,
        )
        self.content = tk.Frame(self.canvas, bg="#171522", padx=18, pady=16)
        self._content_window = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw",
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)

    def _update_scroll_region(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self._content_window, width=event.width)


def open_settings_dialog(
    parent,
    persona,
    preferences,
    on_saved,
    prompted_by_send=False,
):
    try:
        has_api_key = load_api_key() is not None
    except CredentialStoreError as error:
        messagebox.showerror("Ключ OpenAI", str(error), parent=parent)
        return

    dialog = tk.Toplevel(parent)
    dialog.title("Настройки Arise")
    dialog.configure(bg="#171522")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.geometry("560x760")

    style = ttk.Style(dialog)
    style.configure(
        "Arise.TNotebook",
        background="#171522",
        borderwidth=0,
    )
    style.configure(
        "Arise.TNotebook.Tab",
        background="#2c2740",
        foreground="#d8cde4",
        padding=(14, 8),
        font=("Segoe UI", 9),
    )
    style.map(
        "Arise.TNotebook.Tab",
        background=[("selected", "#453952")],
        foreground=[("selected", "#f4efff")],
    )

    notebook = ttk.Notebook(dialog, style="Arise.TNotebook")
    notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    ai_tab = ScrollableTab(notebook)
    communication_tab = ScrollableTab(notebook)
    behavior_tab = ScrollableTab(notebook)
    notebook.add(ai_tab, text="ИИ")
    notebook.add(communication_tab, text="Общение")
    notebook.add(behavior_tab, text="Поведение")

    ai_content = ai_tab.content
    tk.Label(
        ai_content,
        text="Поставщик ИИ",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w")
    provider_var = tk.StringVar(dialog, value=preferences["ai_provider"])
    for value, label in (
        ("ollama", "Ollama — локально на этом компьютере"),
        ("openai", "OpenAI API"),
    ):
        tk.Radiobutton(
            ai_content,
            text=label,
            variable=provider_var,
            value=value,
            bg="#171522",
            fg="#d8cde4",
            activebackground="#171522",
            activeforeground="#f4efff",
            selectcolor="#2c2740",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

    tk.Label(
        ai_content,
        text="Модель Ollama",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 9, "bold"),
    ).pack(anchor="w", pady=(10, 3))
    model_entry = tk.Entry(
        ai_content,
        bg="#2c2740",
        fg="#f4efff",
        insertbackground="#f4efff",
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    model_entry.pack(fill="x", ipady=6, pady=(0, 18))
    model_entry.insert(0, preferences["ollama_model"])

    tk.Label(
        ai_content,
        text="Ключ OpenAI API",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w")
    tk.Label(
        ai_content,
        text=(
            "Нужен только при выборе OpenAI API. Ключ шифруется Windows и хранится "
            "только на этом компьютере. Оставь поле пустым, чтобы не менять его."
            if has_api_key
            else "Если выберешь OpenAI, ключ будет зашифрован Windows и сохранён "
            "только на этом компьютере."
        ),
        bg="#171522",
        fg="#aaa2bd",
        wraplength=460,
        justify="left",
        font=("Segoe UI", 9),
    ).pack(anchor="w", pady=(5, 10))
    key_entry = tk.Entry(
        ai_content,
        show="*",
        bg="#2c2740",
        fg="#f4efff",
        insertbackground="#f4efff",
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    key_entry.pack(fill="x", ipady=8, pady=(0, 16))
    clear_key_var = tk.BooleanVar(dialog, value=False)
    if has_api_key:
        tk.Checkbutton(
            ai_content,
            text="Удалить сохранённый API-ключ",
            variable=clear_key_var,
            bg="#171522",
            fg="#d8cde4",
            activebackground="#171522",
            activeforeground="#f4efff",
            selectcolor="#2c2740",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 12))

    communication_content = communication_tab.content
    tk.Label(
        communication_content,
        text="Характер Arise",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w")
    persona_input = tk.Text(
        communication_content,
        height=5,
        bg="#2c2740",
        fg="#f4efff",
        insertbackground="#f4efff",
        relief="flat",
        borderwidth=0,
        wrap="word",
        font=("Segoe UI", 9),
    )
    persona_input.pack(fill="x", pady=(8, 18))
    persona_input.insert("1.0", persona)

    tk.Label(
        communication_content,
        text="Качества общения (0–100)",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w", pady=(0, 4))
    communication_vars = {
        name: tk.IntVar(dialog, value=value)
        for name, value in preferences["communication_style"].items()
    }
    for name, label in (
        ("conciseness", "Краткость · подробно — коротко"),
        ("warmth", "Теплота · сдержанно — заботливо"),
        ("humor", "Юмор · редко — часто"),
        ("energy", "Энергичность · спокойно — оживлённо"),
    ):
        tk.Scale(
            communication_content,
            label=label,
            variable=communication_vars[name],
            from_=0,
            to=100,
            resolution=5,
            orient="horizontal",
            showvalue=True,
            bg="#171522",
            fg="#d8cde4",
            activebackground="#e9a6d7",
            troughcolor="#2c2740",
            highlightthickness=0,
            sliderrelief="flat",
            font=("Segoe UI", 8),
        ).pack(fill="x", pady=(0, 6))

    behavior_content = behavior_tab.content
    tk.Label(
        behavior_content,
        text="Поведение",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w", pady=(0, 8))
    preference_vars = {
        "follow_cursor": tk.BooleanVar(
            dialog,
            value=preferences["follow_cursor"],
        ),
        "animate_on_click": tk.BooleanVar(
            dialog,
            value=preferences["animate_on_click"],
        ),
        "greet_on_start": tk.BooleanVar(
            dialog,
            value=preferences["greet_on_start"],
        ),
    }
    for name, label in (
        ("follow_cursor", "Следить глазами и головой за курсором"),
        ("animate_on_click", "Случайное движение при одиночном нажатии"),
        ("greet_on_start", "Проигрывать анимацию приветствия при появлении"),
    ):
        tk.Checkbutton(
            behavior_content,
            text=label,
            variable=preference_vars[name],
            bg="#171522",
            fg="#d8cde4",
            activebackground="#171522",
            activeforeground="#f4efff",
            selectcolor="#2c2740",
            font=("Segoe UI", 9),
            wraplength=460,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

    def save_settings():
        updated_persona = persona_input.get("1.0", "end-1c").strip()
        api_key = key_entry.get().strip()
        if not updated_persona:
            messagebox.showerror(
                "Настройки Arise",
                "Описание личности не может быть пустым.",
                parent=dialog,
            )
            return

        try:
            if api_key:
                save_api_key(api_key)
            elif clear_key_var.get():
                delete_api_key()
            updated_preferences = {
                name: variable.get()
                for name, variable in preference_vars.items()
            }
            updated_preferences["ai_provider"] = provider_var.get()
            updated_preferences["ollama_model"] = (
                model_entry.get().strip()
                or preferences["ollama_model"]
            )
            updated_preferences["communication_style"] = {
                name: variable.get()
                for name, variable in communication_vars.items()
            }
            if (
                updated_preferences["ai_provider"] == "ollama"
                and not model_entry.get().strip()
            ):
                messagebox.showerror(
                    "Настройки Arise",
                    "Укажи название установленной модели Ollama.",
                    parent=dialog,
                )
                return
            save_preferences(updated_persona, **updated_preferences)
            saved_api_key = load_api_key()
            if api_key and saved_api_key != api_key:
                raise CredentialStoreError(
                    "Проверка сохранённого API-ключа не прошла."
                )
        except (CredentialStoreError, SettingsError) as error:
            messagebox.showerror("Настройки Arise", str(error), parent=dialog)
            return

        on_saved(
            updated_persona,
            saved_api_key is not None,
            updated_preferences,
        )
        dialog.destroy()
        if not prompted_by_send:
            if updated_preferences["ai_provider"] == "ollama":
                confirmation = (
                    "Настройки сохранены. Сохранение не отправляет запрос; "
                    "следующее сообщение получит ответ от Ollama."
                )
            elif saved_api_key is not None:
                confirmation = (
                    "Настройки сохранены. Сохранение не отправляет запрос к API. "
                    "Отправь сообщение, чтобы получить ответ."
                )
            else:
                confirmation = "Характер сохранён. Добавь API-ключ, чтобы включить чат."
            messagebox.showinfo(
                "Настройки Arise",
                confirmation,
                parent=parent,
            )

    buttons = tk.Frame(dialog, bg="#171522", padx=10, pady=10)
    buttons.pack(fill="x")
    tk.Button(
        buttons,
        text="Отмена",
        command=dialog.destroy,
        bg="#2c2740",
        fg="#f4efff",
        activebackground="#211e30",
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 9),
        cursor="hand2",
        padx=14,
        pady=8,
    ).pack(side="right", padx=(8, 0))
    tk.Button(
        buttons,
        text="Сохранить",
        command=save_settings,
        bg="#e9a6d7",
        fg="#241a2c",
        activebackground="#f2bce4",
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 9, "bold"),
        cursor="hand2",
        padx=14,
        pady=8,
    ).pack(side="right")
    key_entry.focus_set()

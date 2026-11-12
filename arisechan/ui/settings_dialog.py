import tkinter as tk
from tkinter import messagebox

from arisechan.storage.credential_store import (
    CredentialStoreError,
    delete_api_key,
    load_api_key,
    save_api_key,
)
from arisechan.storage.settings_store import SettingsError, save_preferences


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
    dialog.geometry("460x620")

    content = tk.Frame(dialog, bg="#171522", padx=18, pady=16)
    content.pack(fill="both", expand=True)
    tk.Label(
        content,
        text="Подключение OpenAI",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w")
    tk.Label(
        content,
        text=(
            "Ключ шифруется Windows и хранится только на этом компьютере. "
            "Оставь поле пустым, чтобы не менять сохранённый ключ."
            if has_api_key
            else "Ключ будет зашифрован Windows и сохранён только на этом компьютере."
        ),
        bg="#171522",
        fg="#aaa2bd",
        wraplength=400,
        justify="left",
        font=("Segoe UI", 9),
    ).pack(anchor="w", pady=(5, 10))
    key_entry = tk.Entry(
        content,
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
            content,
            text="Удалить сохранённый API-ключ",
            variable=clear_key_var,
            bg="#171522",
            fg="#d8cde4",
            activebackground="#171522",
            activeforeground="#f4efff",
            selectcolor="#2c2740",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Характер Arise",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w")
    persona_input = tk.Text(
        content,
        height=6,
        bg="#2c2740",
        fg="#f4efff",
        insertbackground="#f4efff",
        relief="flat",
        borderwidth=0,
        wrap="word",
        font=("Segoe UI", 9),
    )
    persona_input.pack(fill="both", expand=True, pady=(8, 14))
    persona_input.insert("1.0", persona)

    tk.Label(
        content,
        text="Поведение",
        bg="#171522",
        fg="#f4efff",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor="w", pady=(0, 4))

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
            content,
            text=label,
            variable=preference_vars[name],
            bg="#171522",
            fg="#d8cde4",
            activebackground="#171522",
            activeforeground="#f4efff",
            selectcolor="#2c2740",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

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
            messagebox.showinfo(
                "Настройки Arise",
                (
                    "Настройки сохранены. Сохранение не отправляет запрос к API. "
                    "Нажми на облачко и отправь сообщение, чтобы получить ответ."
                    if saved_api_key is not None
                    else "Характер сохранён. Добавь API-ключ, чтобы включить чат."
                ),
                parent=parent,
            )

    buttons = tk.Frame(content, bg="#171522")
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

"""Persistent, non-secret Arise preferences."""

import json
import os
from pathlib import Path


DEFAULT_PERSONA = (
    "Ты Arise — самостоятельный AI-компаньон. Общайся тепло и заботливо, "
    "добавляй лёгкий юмор и отвечай по делу. Не выдавай себя за человека. "
    "Если чего-то не знаешь — честно скажи. У тебя пока нет инструментов "
    "для чтения или изменения файлов, поэтому не утверждай, что выполнила "
    "такие действия."
)
DEFAULT_PREFERENCES = {
    "persona": DEFAULT_PERSONA,
    "follow_cursor": True,
    "animate_on_click": True,
    "greet_on_start": True,
}


class SettingsError(RuntimeError):
    pass


def _settings_path():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise SettingsError("Windows не указал папку AppData.")
    return Path(appdata) / "AriseChan" / "settings.json"


def load_preferences():
    path = _settings_path()
    if not path.exists():
        return DEFAULT_PREFERENCES.copy()

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SettingsError(f"Не удалось прочитать настройки Arise: {error}") from error

    if not isinstance(settings, dict):
        raise SettingsError("Файл настроек Arise должен содержать объект JSON.")

    persona = settings.get("persona")
    if not isinstance(persona, str) or not persona.strip():
        raise SettingsError("В настройках Arise отсутствует текст личности.")

    preferences = {"persona": persona.strip()}
    for name in ("follow_cursor", "animate_on_click", "greet_on_start"):
        value = settings.get(name, DEFAULT_PREFERENCES[name])
        if type(value) is not bool:
            raise SettingsError(f"Параметр «{name}» должен иметь логическое значение.")
        preferences[name] = value
    return preferences


def load_persona():
    return load_preferences()["persona"]


def _write_preferences(preferences):
    try:
        path = _settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(preferences, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(path)
    except OSError as error:
        raise SettingsError(f"Не удалось сохранить настройки Arise: {error}") from error


def save_preferences(persona, follow_cursor, animate_on_click, greet_on_start):
    if not persona.strip():
        raise SettingsError("Описание личности не может быть пустым.")
    values = {
        "follow_cursor": follow_cursor,
        "animate_on_click": animate_on_click,
        "greet_on_start": greet_on_start,
    }
    if any(type(value) is not bool for value in values.values()):
        raise SettingsError("Параметры Arise должны иметь логические значения.")

    _write_preferences({"persona": persona.strip(), **values})


def save_persona(persona):
    preferences = load_preferences()
    save_preferences(
        persona,
        preferences["follow_cursor"],
        preferences["animate_on_click"],
        preferences["greet_on_start"],
    )

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


class SettingsError(RuntimeError):
    pass


def _settings_path():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise SettingsError("Windows не указал папку AppData.")
    return Path(appdata) / "AriseChan" / "settings.json"


def load_persona():
    path = _settings_path()
    if not path.exists():
        return DEFAULT_PERSONA

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SettingsError(f"Не удалось прочитать настройки Arise: {error}") from error

    persona = settings.get("persona") if isinstance(settings, dict) else None
    if not isinstance(persona, str) or not persona.strip():
        raise SettingsError("В настройках Arise отсутствует текст личности.")
    return persona.strip()


def save_persona(persona):
    if not persona.strip():
        raise SettingsError("Описание личности не может быть пустым.")

    try:
        path = _settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps({"persona": persona.strip()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(path)
    except OSError as error:
        raise SettingsError(f"Не удалось сохранить настройки Arise: {error}") from error

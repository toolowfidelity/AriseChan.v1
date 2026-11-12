"""User-scoped Windows DPAPI storage for the OpenAI API key."""

import ctypes
import os
from ctypes import wintypes
from pathlib import Path


class CredentialStoreError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _credential_path():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise CredentialStoreError("Windows не указал папку AppData.")
    return Path(appdata) / "AriseChan" / "openai-key.bin"


def _transform(data, decrypt):
    if os.name != "nt":
        raise CredentialStoreError("Хранилище ключа доступно только в Windows.")

    crypt32 = ctypes.WinDLL("crypt32.dll", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
    blob_pointer = ctypes.POINTER(_DataBlob)
    source_buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source_blob = _DataBlob(
        len(data),
        ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    result_blob = _DataBlob()

    if decrypt:
        transform = crypt32.CryptUnprotectData
        transform.restype = wintypes.BOOL
        transform.argtypes = [
            blob_pointer,
            ctypes.POINTER(wintypes.LPWSTR),
            blob_pointer,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            blob_pointer,
        ]
        succeeded = transform(
            ctypes.byref(source_blob),
            None,
            None,
            None,
            None,
            1,
            ctypes.byref(result_blob),
        )
    else:
        transform = crypt32.CryptProtectData
        transform.restype = wintypes.BOOL
        transform.argtypes = [
            blob_pointer,
            wintypes.LPCWSTR,
            blob_pointer,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            blob_pointer,
        ]
        succeeded = transform(
            ctypes.byref(source_blob),
            "AriseChan OpenAI API key",
            None,
            None,
            None,
            1,
            ctypes.byref(result_blob),
        )

    if not succeeded:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(result_blob.pbData, result_blob.cbData)
    finally:
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        kernel32.LocalFree(ctypes.cast(result_blob.pbData, ctypes.c_void_p))


def save_api_key(api_key):
    if not api_key.strip():
        raise CredentialStoreError("API-ключ не может быть пустым.")
    try:
        encrypted = _transform(api_key.encode("utf-8"), decrypt=False)
        path = _credential_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_bytes(encrypted)
        temporary_path.replace(path)
    except (OSError, UnicodeEncodeError) as error:
        raise CredentialStoreError(f"Не удалось сохранить API-ключ: {error}") from error


def load_api_key():
    try:
        path = _credential_path()
        if not path.exists():
            return None
        encrypted = path.read_bytes()
        return _transform(encrypted, decrypt=True).decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise CredentialStoreError(f"Не удалось прочитать API-ключ: {error}") from error

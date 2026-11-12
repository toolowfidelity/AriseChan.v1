"""Client for a locally running Ollama server."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3:4b"
REQUEST_TIMEOUT_SECONDS = 180


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, model=DEFAULT_MODEL):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An Ollama model name is required.")
        self.model = model.strip()

    def reply(self, messages):
        body = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "think": False,
                "keep_alive": "1m",
                "options": {
                    "num_ctx": 4096,
                    "num_predict": 512,
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            API_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = self._http_error_detail(error)
            raise OllamaError(
                f"Ollama вернул ошибку {error.code}: {detail}"
            ) from error
        except (URLError, TimeoutError) as error:
            raise OllamaError(
                "Не удалось подключиться к локальному Ollama. "
                "Проверь, что Ollama запущена."
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OllamaError("Ollama вернул некорректный ответ.") from error

        try:
            content = payload["message"]["content"]
        except (KeyError, TypeError) as error:
            raise OllamaError("В ответе Ollama нет текста сообщения.") from error

        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama вернул пустой ответ.")
        return content.strip()

    @staticmethod
    def _http_error_detail(error):
        try:
            payload = json.loads(error.read().decode("utf-8"))
            detail = payload.get("error")
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
            detail = None
        return detail or str(error.reason)

"""Client for a locally running Ollama server."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3:1.7b"
REQUEST_TIMEOUT_SECONDS = 180
DEFAULT_NUM_PREDICT = 128
MIN_NUM_PREDICT = 64
MAX_NUM_PREDICT = 256


class OllamaError(RuntimeError):
    pass


def num_predict_for_conciseness(value):
    if type(value) is not int or not 0 <= value <= 100:
        raise ValueError("Conciseness must be an integer from 0 to 100.")
    return MIN_NUM_PREDICT + round(
        (MAX_NUM_PREDICT - MIN_NUM_PREDICT) * (100 - value) / 100
    )


class OllamaClient:
    def __init__(self, model=DEFAULT_MODEL, num_predict=DEFAULT_NUM_PREDICT):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An Ollama model name is required.")
        if (
            type(num_predict) is not int
            or not MIN_NUM_PREDICT <= num_predict <= MAX_NUM_PREDICT
        ):
            raise ValueError(
                f"num_predict must be between {MIN_NUM_PREDICT} and "
                f"{MAX_NUM_PREDICT}."
            )
        self.model = model.strip()
        self.num_predict = num_predict

    def reply(self, messages):
        body = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "think": False,
                "keep_alive": "5m",
                "options": {
                    "num_ctx": 2048,
                    "num_predict": self.num_predict,
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

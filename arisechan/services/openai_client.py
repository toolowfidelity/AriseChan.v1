"""OpenAI chat-completions API client."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MODEL = "gpt-4o-mini"
API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIError(RuntimeError):
    pass


class OpenAIClient:
    def __init__(self, api_key, model=MODEL):
        if not api_key.strip():
            raise ValueError("An OpenAI API key is required.")
        self.api_key = api_key
        self.model = model

    def reply(self, messages):
        body = json.dumps(
            {"model": self.model, "messages": messages},
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = self._http_error_detail(error)
            raise OpenAIError(
                f"OpenAI API вернул ошибку {error.code}: {detail}"
            ) from error
        except (URLError, TimeoutError) as error:
            raise OpenAIError(
                f"Не удалось подключиться к OpenAI API: {error}"
            ) from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OpenAIError("OpenAI API вернул некорректный ответ.") from error

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise OpenAIError("В ответе OpenAI API нет текста сообщения.") from error

        if not isinstance(content, str) or not content.strip():
            raise OpenAIError("OpenAI API вернул пустой ответ.")
        return content.strip()

    @staticmethod
    def _http_error_detail(error):
        try:
            payload = json.loads(error.read().decode("utf-8"))
            detail = payload.get("error", {}).get("message")
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
            detail = None
        return detail or str(error.reason)

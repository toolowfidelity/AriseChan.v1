import json
import unittest
from io import BytesIO
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from arisechan.services.ollama_client import OllamaClient, OllamaError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class OllamaClientTests(unittest.TestCase):
    @patch("arisechan.services.ollama_client.urlopen")
    def test_sends_local_chat_request_without_thinking(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            {"message": {"role": "assistant", "content": "Привет!"}}
        )
        messages = [{"role": "user", "content": "Привет"}]

        answer = OllamaClient("qwen3:4b").reply(messages)

        self.assertEqual(answer, "Привет!")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "qwen3:4b")
        self.assertEqual(payload["messages"], messages)
        self.assertFalse(payload["think"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertEqual(payload["options"]["num_predict"], 256)

    @patch("arisechan.services.ollama_client.urlopen")
    def test_reports_ollama_api_errors(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "http://localhost:11434/api/chat",
            404,
            "Not Found",
            None,
            BytesIO(b'{"error":"model not found"}'),
        )

        with self.assertRaisesRegex(OllamaError, "model not found"):
            OllamaClient().reply([{"role": "user", "content": "Hi"}])

    @patch("arisechan.services.ollama_client.urlopen")
    def test_reports_server_connection_errors(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("connection refused")

        with self.assertRaisesRegex(OllamaError, "Ollama"):
            OllamaClient().reply([{"role": "user", "content": "Hi"}])

    def test_rejects_empty_model_name(self):
        with self.assertRaises(ValueError):
            OllamaClient(" ")


if __name__ == "__main__":
    unittest.main()

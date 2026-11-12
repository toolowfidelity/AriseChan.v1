import json
import unittest
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

from arisechan.services.openai_client import OpenAIClient, OpenAIError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class OpenAIClientTests(unittest.TestCase):
    @patch("arisechan.services.openai_client.urlopen")
    def test_sends_messages_and_returns_assistant_text(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            {"choices": [{"message": {"content": "Привет!"}}]}
        )

        answer = OpenAIClient("test-key").reply(
            [{"role": "user", "content": "Привет"}]
        )

        self.assertEqual(answer, "Привет!")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(
            json.loads(request.data)["messages"],
            [{"role": "user", "content": "Привет"}],
        )

    @patch("arisechan.services.openai_client.urlopen")
    def test_reports_api_error_without_hiding_message(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            "https://api.openai.com/v1/chat/completions",
            401,
            "Unauthorized",
            None,
            BytesIO(b'{"error":{"message":"Invalid API key"}}'),
        )

        with self.assertRaisesRegex(OpenAIError, "Invalid API key"):
            OpenAIClient("test-key").reply(
                [{"role": "user", "content": "Hello"}]
            )

    def test_rejects_empty_api_key(self):
        with self.assertRaises(ValueError):
            OpenAIClient(" ")


if __name__ == "__main__":
    unittest.main()

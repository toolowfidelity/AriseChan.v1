import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arisechan.storage.credential_store import delete_api_key


class CredentialStoreTests(unittest.TestCase):
    def test_delete_api_key_removes_existing_credential(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "openai-key.bin"
            path.write_bytes(b"encrypted")
            with patch(
                "arisechan.storage.credential_store._credential_path",
                return_value=path,
            ):
                delete_api_key()

            self.assertFalse(path.exists())

    def test_delete_api_key_is_safe_when_no_credential_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing-key.bin"
            with patch(
                "arisechan.storage.credential_store._credential_path",
                return_value=path,
            ):
                delete_api_key()

            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()

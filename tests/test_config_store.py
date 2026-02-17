import tempfile
import unittest
from pathlib import Path

from spec_engine.config_store import get_api_key, set_api_key


class ConfigStoreTests(unittest.TestCase):
    def test_set_and_get_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td)
            set_api_key("openai", "sk-test", base_dir=base_dir)
            value = get_api_key("openai", base_dir=base_dir)
            self.assertEqual(value, "sk-test")


if __name__ == "__main__":
    unittest.main()


import os
import unittest
from unittest.mock import patch

from spec_engine.providers import ProviderError, resolve_llm_client_config


class ProviderConfigTests(unittest.TestCase):
    def test_openrouter_key_takes_precedence(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "or-key",
                "OPENAI_API_KEY": "oa-key",
            },
            clear=False,
        ):
            cfg = resolve_llm_client_config()
        self.assertEqual(cfg["api_key"], "or-key")
        self.assertEqual(cfg["base_url"], "https://openrouter.ai/api/v1")

    def test_openai_key_used_when_openrouter_missing(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "oa-key"}, clear=True):
            cfg = resolve_llm_client_config()
        self.assertEqual(cfg, {"api_key": "oa-key"})

    def test_missing_keys_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderError):
                resolve_llm_client_config()

    def test_explicit_openrouter_config(self) -> None:
        cfg = resolve_llm_client_config(provider_name="openrouter", api_key="sk-or-test")
        self.assertEqual(cfg["api_key"], "sk-or-test")
        self.assertEqual(cfg["base_url"], "https://openrouter.ai/api/v1")


if __name__ == "__main__":
    unittest.main()

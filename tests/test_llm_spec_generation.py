import json
import tempfile
import unittest
from pathlib import Path

from spec_engine.cli import _generate_spec
from spec_engine.models import FieldCandidate, SpecDraft
from spec_engine.renderer import render_spec_markdown


class FakeLLMProvider:
    is_llm_provider = True

    def __init__(self) -> None:
        self.generate_spec_called = 0

    def extract_requirements(self, prompt: str) -> SpecDraft:
        return SpecDraft(
            project_name=FieldCandidate("Demo", 1.0, "seed"),
            project_type=FieldCandidate("CLI tool", 1.0, "seed"),
            primary_goal=FieldCandidate("Generate specs", 1.0, "seed"),
            target_users=FieldCandidate("Developers", 1.0, "seed"),
            inputs=FieldCandidate("Prompt text", 1.0, "seed"),
            outputs=FieldCandidate("SPEC markdown", 1.0, "seed"),
            constraints=FieldCandidate("Python 3.10+", 1.0, "seed"),
            non_goals=FieldCandidate("No GUI", 1.0, "seed"),
        )

    def generate_followup(self, missing_field: str, draft: SpecDraft) -> str:
        return f"Question for {missing_field}?"

    def normalize_spec(self, draft: SpecDraft) -> SpecDraft:
        return draft

    def generate_spec_markdown(self, draft: SpecDraft) -> str:
        self.generate_spec_called += 1
        return render_spec_markdown(draft)


class LLMGenerationTests(unittest.TestCase):
    def test_markdown_generation_uses_llm_generator(self) -> None:
        provider = FakeLLMProvider()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "SPEC.md"
            result = _generate_spec(
                prompt="Build something",
                output=str(out),
                as_json=False,
                interactive=False,
                provider=provider,
            )
            self.assertIsNone(result)
            self.assertEqual(provider.generate_spec_called, 1)
            self.assertTrue(out.exists())

    def test_json_generation_does_not_use_llm_markdown_generator(self) -> None:
        provider = FakeLLMProvider()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "SPEC.json"
            result = _generate_spec(
                prompt="Build something",
                output=str(out),
                as_json=True,
                interactive=False,
                provider=provider,
            )
            self.assertIsNone(result)
            self.assertEqual(provider.generate_spec_called, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("fields", payload)


if __name__ == "__main__":
    unittest.main()


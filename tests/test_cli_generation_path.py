import tempfile
import unittest
from pathlib import Path

from spec_engine.cli import _generate_spec
from spec_engine.models import FieldCandidate, SpecDraft


class FakeLLMProvider:
    is_llm_provider = True

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
        return "# Project Specification\n\nLLM Output\n"


class CLIGenerationPathTests(unittest.TestCase):
    def test_generate_uses_llm_markdown_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "SPEC.md"
            result = _generate_spec(
                prompt="Build a tool",
                output=str(out),
                as_json=False,
                interactive=False,
                provider=FakeLLMProvider(),
            )
            self.assertIsNone(result)
            self.assertEqual(out.read_text(encoding="utf-8"), "# Project Specification\n\nLLM Output\n")

    def test_generate_uses_renderer_without_llm(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "SPEC.md"
            result = _generate_spec(
                prompt=(
                    "Project Name: Demo\n"
                    "Project Type: CLI tool\n"
                    "Primary Goal: Generate specs.\n"
                    "Target Users: Developers.\n"
                    "Inputs: Prompt text.\n"
                    "Outputs: SPEC markdown.\n"
                    "Constraints: Python 3.10+.\n"
                    "Non-Goals: No GUI.\n"
                ),
                output=str(out),
                as_json=False,
                interactive=False,
                provider=None,
            )
            self.assertIsNone(result)
            rendered = out.read_text(encoding="utf-8")
            self.assertIn("## 1. Overview", rendered)


if __name__ == "__main__":
    unittest.main()


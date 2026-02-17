import unittest

from spec_engine.engine import build_spec_draft
from spec_engine.models import FieldCandidate, SpecDraft


class FakeProvider:
    def __init__(self) -> None:
        self.followup_calls: list[str] = []

    def extract_requirements(self, prompt: str) -> SpecDraft:
        return SpecDraft(
            project_name=FieldCandidate("Demo", 1.0, "seed"),
            project_type=FieldCandidate("", 0.0, "missing"),
            primary_goal=FieldCandidate("Ship MVP", 0.9, "seed"),
            target_users=FieldCandidate("", 0.0, "missing"),
            inputs=FieldCandidate("", 0.0, "missing"),
            outputs=FieldCandidate("", 0.0, "missing"),
            constraints=FieldCandidate("", 0.0, "missing"),
            non_goals=FieldCandidate("", 0.0, "missing"),
        )

    def generate_followup(self, missing_field: str, draft: SpecDraft) -> str:
        self.followup_calls.append(missing_field)
        return f"Question for {missing_field}?"

    def normalize_spec(self, draft: SpecDraft) -> SpecDraft:
        return draft


class EngineTests(unittest.TestCase):
    def test_provider_followups_are_sequential_single_field(self) -> None:
        provider = FakeProvider()
        answers = {
            "Question for project_type?": "CLI tool",
            "Question for target_users?": "Developers",
            "Question for inputs?": "Prompt text",
            "Question for outputs?": "SPEC markdown",
            "Question for constraints?": "Python 3.10+",
            "Question for non_goals?": "No GUI",
        }

        def ask_fn(question: str) -> str:
            return answers[question]

        result = build_spec_draft(
            prompt="irrelevant",
            interactive=True,
            provider=provider,
            ask_fn=ask_fn,
        )

        self.assertEqual(
            provider.followup_calls,
            ["project_type", "target_users", "inputs", "outputs", "constraints", "non_goals"],
        )
        self.assertEqual(result.missing_fields, [])


if __name__ == "__main__":
    unittest.main()


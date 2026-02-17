import unittest

from spec_engine.models import FieldCandidate, SpecDraft
from spec_engine.renderer import render_spec_markdown


class RendererTests(unittest.TestCase):
    def test_renderer_uses_required_headings(self) -> None:
        draft = SpecDraft(
            project_name=FieldCandidate("CSV Guard", 1.0, "test"),
            project_type=FieldCandidate("CLI tool", 1.0, "test"),
            primary_goal=FieldCandidate("Validate CSV files from the command line.", 1.0, "test"),
            target_users=FieldCandidate("Developers and data operators.", 1.0, "test"),
            inputs=FieldCandidate("CLI args and CSV files.", 1.0, "test"),
            outputs=FieldCandidate("Validation report in terminal.", 1.0, "test"),
            constraints=FieldCandidate("Python 3.10+, security checks on file paths.", 1.0, "test"),
            non_goals=FieldCandidate("No GUI, no remote storage sync.", 1.0, "test"),
        )

        rendered = render_spec_markdown(draft)
        self.assertIn("# Project Specification", rendered)
        self.assertIn("## 1. Overview", rendered)
        self.assertIn("## 10. Acceptance Criteria", rendered)


if __name__ == "__main__":
    unittest.main()

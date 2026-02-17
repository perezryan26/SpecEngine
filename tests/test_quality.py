import unittest

from spec_engine.models import FieldCandidate, SpecDraft
from spec_engine.quality import coerce_to_list_markdown, validate_spec_markdown
from spec_engine.renderer import render_spec_markdown


class QualityTests(unittest.TestCase):
    def test_renderer_output_passes_quality_validation(self) -> None:
        draft = SpecDraft(
            project_name=FieldCandidate("CSV Guard", 1.0, "test"),
            project_type=FieldCandidate("CLI tool", 1.0, "test"),
            primary_goal=FieldCandidate("Validate CSV files.", 1.0, "test"),
            target_users=FieldCandidate("Developers.", 1.0, "test"),
            inputs=FieldCandidate("CLI args and CSV file paths.", 1.0, "test"),
            outputs=FieldCandidate("Terminal validation report.", 1.0, "test"),
            constraints=FieldCandidate("Python 3.10+.", 1.0, "test"),
            non_goals=FieldCandidate("No GUI.", 1.0, "test"),
        )
        content = render_spec_markdown(draft)
        self.assertEqual(validate_spec_markdown(content), [])

    def test_invalid_heading_order_fails(self) -> None:
        content = (
            "# Project Specification\n\n"
            "## 2. Problem Statement\n"
            "- Wrong order.\n"
        )
        errors = validate_spec_markdown(content)
        self.assertTrue(any("Headings must match strict required structure and ordering." in e for e in errors))

    def test_non_list_prose_fails(self) -> None:
        content = (
            "# Project Specification\n\n"
            "## 1. Overview\n"
            "This is free prose.\n"
        )
        errors = validate_spec_markdown(content)
        self.assertTrue(any("unsupported formatting" in e for e in errors))

    def test_coerce_converts_prose_to_bullets(self) -> None:
        content = (
            "# Project Specification\n\n"
            "## 1. Overview\n"
            "Plain prose line.\n"
            "## 2. Problem Statement\n"
            "Another prose line.\n"
            "## 3. Scope\n"
            "### In Scope\n"
            "Thing one\n"
            "### Out of Scope\n"
            "Thing two\n"
            "## 4. Functional Requirements\n"
            "1. Keep this number.\n"
            "## 5. Non-Functional Requirements\n"
            "Reliability text.\n"
            "## 6. Inputs\n"
            "Input text.\n"
            "## 7. Outputs\n"
            "Output text.\n"
            "## 8. Constraints\n"
            "Constraint text.\n"
            "## 9. Assumptions\n"
            "Assumption text.\n"
            "## 10. Acceptance Criteria\n"
            "Criteria text.\n"
        )
        coerced = coerce_to_list_markdown(content)
        self.assertIn("- Plain prose line.", coerced)
        self.assertIn("1. Keep this number.", coerced)
        self.assertEqual(validate_spec_markdown(coerced), [])


if __name__ == "__main__":
    unittest.main()

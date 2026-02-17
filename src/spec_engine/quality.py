from __future__ import annotations

import re

EXPECTED_HEADINGS = [
    "# Project Specification",
    "## 1. Overview",
    "## 2. Problem Statement",
    "## 3. Scope",
    "### In Scope",
    "### Out of Scope",
    "## 4. Functional Requirements",
    "## 5. Non-Functional Requirements",
    "## 6. Inputs",
    "## 7. Outputs",
    "## 8. Constraints",
    "## 9. Assumptions",
    "## 10. Acceptance Criteria",
]


def validate_spec_markdown(content: str) -> list[str]:
    errors: list[str] = []
    lines = content.splitlines()

    first_non_empty = next((line.strip() for line in lines if line.strip()), "")
    if first_non_empty != "# Project Specification":
        errors.append("First non-empty line must be '# Project Specification'.")

    headings = [line.strip() for line in lines if line.strip().startswith("#")]
    if headings != EXPECTED_HEADINGS:
        errors.append("Headings must match strict required structure and ordering.")

    allowed_prefix = re.compile(r"^(#|-\s|\d+\.\s)")
    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        if not allowed_prefix.match(line):
            errors.append(f"Line {index} contains non-list prose or unsupported formatting: {line}")

    return errors


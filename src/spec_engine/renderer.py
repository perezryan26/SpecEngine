from __future__ import annotations

from .models import SpecDraft


def render_spec_markdown(draft: SpecDraft) -> str:
    project_name = draft.project_name.value
    project_type = draft.project_type.value
    primary_goal = draft.primary_goal.value
    target_users = draft.target_users.value
    inputs = draft.inputs.value
    outputs = draft.outputs.value
    constraints = draft.constraints.value
    non_goals = draft.non_goals.value

    in_scope_items = _split_to_bullets(
        f"Deliver core {project_type} behavior aligned to goal: {primary_goal}. "
        f"Support primary user group: {target_users}. "
        f"Handle defined inputs and produce defined outputs."
    )
    out_of_scope_items = _split_to_bullets(non_goals)
    functional_requirements = _default_functional_requirements(inputs, outputs, primary_goal)
    non_functional = _default_non_functional_requirements(constraints)
    acceptance_criteria = _default_acceptance_criteria(project_name, outputs)

    sections = [
        "# Project Specification",
        "",
        "## 1. Overview",
        f"- Project Name: {project_name}",
        f"- Project Type: {project_type}",
        f"- Primary Goal: {primary_goal}",
        f"- Target Users: {target_users}",
        "",
        "## 2. Problem Statement",
        f"- The current workflow does not reliably satisfy this objective: {primary_goal}.",
        "",
        "## 3. Scope",
        "### In Scope",
        *[f"- {item}" for item in in_scope_items],
        "",
        "### Out of Scope",
        *[f"- {item}" for item in out_of_scope_items],
        "",
        "## 4. Functional Requirements",
        *[f"{idx}. {item}" for idx, item in enumerate(functional_requirements, start=1)],
        "",
        "## 5. Non-Functional Requirements",
        *[f"- {item}" for item in non_functional],
        "",
        "## 6. Inputs",
        f"- {inputs}",
        "",
        "## 7. Outputs",
        f"- {outputs}",
        "",
        "## 8. Constraints",
        f"- {constraints}",
        "",
        "## 9. Assumptions",
        "- User-provided answers are accurate and complete at generation time.",
        "- Requirements may require refinement if domain constraints change.",
        "",
        "## 10. Acceptance Criteria",
        *[f"- {item}" for item in acceptance_criteria],
    ]
    return "\n".join(sections) + "\n"


def _split_to_bullets(value: str) -> list[str]:
    parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    return parts if parts else ["None specified."]


def _default_functional_requirements(inputs: str, outputs: str, primary_goal: str) -> list[str]:
    return [
        f"The system SHALL accept and validate the defined inputs: {inputs}.",
        f"The system SHALL produce outputs in the defined format: {outputs}.",
        f"The system SHALL implement behavior that directly supports this goal: {primary_goal}.",
        "The system SHALL return deterministic results for identical valid inputs.",
    ]


def _default_non_functional_requirements(constraints: str) -> list[str]:
    items = []
    lowered = constraints.lower()
    if any(token in lowered for token in ("performance", "latency", "throughput", "fast")):
        items.append("Performance: Must satisfy declared performance expectations.")
    if any(token in lowered for token in ("reliable", "availability", "uptime", "fault")):
        items.append("Reliability: Must handle errors predictably and recover safely.")
    if any(token in lowered for token in ("security", "auth", "encryption", "privacy")):
        items.append("Security: Must enforce relevant security controls and data protections.")
    if any(token in lowered for token in ("maintain", "readable", "modular", "test")):
        items.append("Maintainability: Code and interfaces must remain testable and maintainable.")
    if not items:
        items.append("Maintainability: Implementation must remain testable and readable.")
    return items


def _default_acceptance_criteria(project_name: str, outputs: str) -> list[str]:
    return [
        f"`{project_name}` generates the expected output: {outputs}.",
        "All required fields are present and non-ambiguous in the generated specification.",
        "The specification follows the mandated section order and headings.",
    ]


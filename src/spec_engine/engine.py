from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import FieldCandidate, REQUIRED_FIELDS, SpecDraft
from .parser import normalize_user_field_value, parse_prompt


FIELD_PROMPTS = {
    "project_name": "What is the project name?",
    "project_type": "What is the project type? (library, service, CLI tool, web app, backend API, frontend UI, full-stack app)",
    "primary_goal": "What is the primary goal in one sentence?",
    "target_users": "Who are the target users?",
    "inputs": "What inputs does the system receive?",
    "outputs": "What outputs does the system produce?",
    "constraints": "What constraints must be followed? (language/runtime/performance/security/platform)",
    "non_goals": "What is explicitly out of scope (non-goals)?",
}


@dataclass
class BuildResult:
    draft: SpecDraft
    missing_fields: list[str]
    ambiguous_fields: list[str]

    def to_json_dict(self) -> dict:
        return {
            "fields": self.draft.as_dict(),
            "missing_fields": self.missing_fields,
            "ambiguous_fields": self.ambiguous_fields,
        }


def build_spec_draft(
    prompt: str,
    interactive: bool,
    ask_fn: Callable[[str], str] | None = None,
) -> BuildResult:
    draft = parse_prompt(prompt)
    if interactive:
        _resolve_gaps_interactively(draft, ask_fn or _default_ask)
    return BuildResult(
        draft=draft,
        missing_fields=draft.missing_fields(),
        ambiguous_fields=draft.ambiguous_fields(),
    )


def _resolve_gaps_interactively(draft: SpecDraft, ask_fn: Callable[[str], str]) -> None:
    for field_name in REQUIRED_FIELDS:
        candidate = getattr(draft, field_name)
        needs_answer = not candidate.value.strip() or candidate.confidence < 0.8
        if not needs_answer:
            continue
        prompt = FIELD_PROMPTS[field_name]
        answer = ask_fn(prompt).strip()
        if not answer:
            continue
        normalized, confidence = normalize_user_field_value(field_name, answer)
        setattr(
            draft,
            field_name,
            FieldCandidate(
                value=normalized,
                confidence=confidence,
                rationale="interactive_user_answer",
            ),
        )


def _default_ask(question: str) -> str:
    return input(f"{question}\n> ")

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import FieldCandidate, REQUIRED_FIELDS, SpecDraft
from .parser import normalize_user_field_value
from .providers import LocalProvider, SpecProvider


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
    provider: SpecProvider | None = None,
    ask_fn: Callable[[str], str] | None = None,
) -> BuildResult:
    selected_provider = provider or LocalProvider()
    draft = selected_provider.extract_requirements(prompt)
    if interactive:
        _resolve_gaps_interactively(draft, selected_provider, ask_fn or _default_ask)
    draft = selected_provider.normalize_spec(draft)
    return BuildResult(
        draft=draft,
        missing_fields=draft.missing_fields(),
        ambiguous_fields=draft.ambiguous_fields(),
    )


def _resolve_gaps_interactively(draft: SpecDraft, provider: SpecProvider, ask_fn: Callable[[str], str]) -> None:
    for field_name in REQUIRED_FIELDS:
        candidate = getattr(draft, field_name)
        needs_answer = not candidate.value.strip() or candidate.confidence < 0.8
        if not needs_answer:
            continue
        prompt = provider.generate_followup(field_name, draft)
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

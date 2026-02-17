from __future__ import annotations

import re
from typing import Dict, Tuple

from .models import FieldCandidate, ProjectType, SpecDraft


LABEL_PATTERNS: Dict[str, re.Pattern[str]] = {
    "project_name": re.compile(r"(?:project\s*name|name)\s*:\s*(.+)", re.IGNORECASE),
    "project_type": re.compile(r"(?:project\s*type|type)\s*:\s*(.+)", re.IGNORECASE),
    "primary_goal": re.compile(r"(?:primary\s*goal|goal)\s*:\s*(.+)", re.IGNORECASE),
    "target_users": re.compile(r"(?:target\s*users|users)\s*:\s*(.+)", re.IGNORECASE),
    "inputs": re.compile(r"(?:inputs?)\s*:\s*(.+)", re.IGNORECASE),
    "outputs": re.compile(r"(?:outputs?)\s*:\s*(.+)", re.IGNORECASE),
    "constraints": re.compile(r"(?:constraints?)\s*:\s*(.+)", re.IGNORECASE),
    "non_goals": re.compile(r"(?:non[-\s]*goals?)\s*:\s*(.+)", re.IGNORECASE),
}


def parse_prompt(prompt: str) -> SpecDraft:
    draft = SpecDraft()
    lines = [line.strip() for line in prompt.splitlines() if line.strip()]
    joined = " ".join(lines)

    for field_name, pattern in LABEL_PATTERNS.items():
        value = _extract_from_lines(lines, pattern)
        if value:
            setattr(draft, field_name, FieldCandidate(value=value, confidence=0.95, rationale="explicit_label"))

    if not draft.project_type.value:
        inferred_type = _infer_project_type(joined)
        if inferred_type:
            draft.project_type = FieldCandidate(value=inferred_type, confidence=0.7, rationale="keyword_inference")

    if not draft.project_name.value:
        name = _infer_project_name(joined)
        if name:
            draft.project_name = FieldCandidate(value=name, confidence=0.55, rationale="title_inference")

    if not draft.primary_goal.value and joined:
        draft.primary_goal = FieldCandidate(value=joined[:220], confidence=0.4, rationale="fallback_prompt_excerpt")

    return draft


def normalize_user_field_value(field_name: str, value: str) -> Tuple[str, float]:
    cleaned = " ".join(value.strip().split())
    if field_name == "project_type":
        for project_type in ProjectType:
            if cleaned.lower() == project_type.value.lower():
                return project_type.value, 1.0
        return cleaned, 0.4
    return cleaned, 1.0 if cleaned else 0.0


def _extract_from_lines(lines: list[str], pattern: re.Pattern[str]) -> str:
    for line in lines:
        match = pattern.search(line)
        if match:
            return match.group(1).strip().rstrip(".")
    return ""


def _infer_project_type(text: str) -> str:
    lowered = text.lower()
    checks = [
        ("full-stack app", ("full stack", "frontend and backend", "end-to-end app")),
        ("backend API", ("api", "endpoint", "rest", "graphql")),
        ("frontend UI", ("frontend", "ui", "single-page", "spa")),
        ("web app", ("web app", "website", "browser app")),
        ("CLI tool", ("cli", "command line", "terminal tool")),
        ("service", ("service", "daemon", "worker")),
        ("library", ("library", "sdk", "package")),
    ]
    for candidate, terms in checks:
        if any(term in lowered for term in terms):
            return candidate
    return ""


def _infer_project_name(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9\-]+", text)
    if not words:
        return ""
    top = words[:4]
    return " ".join(w.capitalize() for w in top)


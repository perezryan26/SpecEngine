from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class ProjectType(str, Enum):
    LIBRARY = "library"
    SERVICE = "service"
    CLI_TOOL = "CLI tool"
    WEB_APP = "web app"
    BACKEND_API = "backend API"
    FRONTEND_UI = "frontend UI"
    FULL_STACK_APP = "full-stack app"


REQUIRED_FIELDS = (
    "project_name",
    "project_type",
    "primary_goal",
    "target_users",
    "inputs",
    "outputs",
    "constraints",
    "non_goals",
)


@dataclass
class FieldCandidate:
    value: str = ""
    confidence: float = 0.0
    rationale: str = ""


@dataclass
class SpecDraft:
    project_name: FieldCandidate = field(default_factory=FieldCandidate)
    project_type: FieldCandidate = field(default_factory=FieldCandidate)
    primary_goal: FieldCandidate = field(default_factory=FieldCandidate)
    target_users: FieldCandidate = field(default_factory=FieldCandidate)
    inputs: FieldCandidate = field(default_factory=FieldCandidate)
    outputs: FieldCandidate = field(default_factory=FieldCandidate)
    constraints: FieldCandidate = field(default_factory=FieldCandidate)
    non_goals: FieldCandidate = field(default_factory=FieldCandidate)

    def as_dict(self) -> Dict[str, Dict[str, str | float]]:
        return {
            name: {
                "value": getattr(self, name).value,
                "confidence": getattr(self, name).confidence,
                "rationale": getattr(self, name).rationale,
            }
            for name in REQUIRED_FIELDS
        }

    def missing_fields(self, min_confidence: float = 0.5) -> List[str]:
        missing: List[str] = []
        for field_name in REQUIRED_FIELDS:
            candidate = getattr(self, field_name)
            if not candidate.value.strip() or candidate.confidence < min_confidence:
                missing.append(field_name)
        return missing

    def ambiguous_fields(self, min_confidence: float = 0.5, accepted_confidence: float = 0.8) -> List[str]:
        ambiguous: List[str] = []
        for field_name in REQUIRED_FIELDS:
            candidate = getattr(self, field_name)
            if candidate.value.strip() and min_confidence <= candidate.confidence < accepted_confidence:
                ambiguous.append(field_name)
        return ambiguous


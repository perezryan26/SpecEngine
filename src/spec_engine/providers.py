from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Protocol

from .models import REQUIRED_FIELDS, SpecDraft
from .parser import parse_prompt


class ProviderError(RuntimeError):
    pass


class SpecProvider(Protocol):
    def extract_requirements(self, prompt: str) -> SpecDraft:
        ...

    def generate_followup(self, missing_field: str, draft: SpecDraft) -> str:
        ...

    def normalize_spec(self, draft: SpecDraft) -> SpecDraft:
        ...


@dataclass
class LocalProvider:
    def extract_requirements(self, prompt: str) -> SpecDraft:
        return parse_prompt(prompt)

    def generate_followup(self, missing_field: str, draft: SpecDraft) -> str:
        prompts = {
            "project_name": "What is the project name?",
            "project_type": "What is the project type? (library, service, CLI tool, web app, backend API, frontend UI, full-stack app)",
            "primary_goal": "What is the primary goal in one sentence?",
            "target_users": "Who are the target users?",
            "inputs": "What inputs does the system receive?",
            "outputs": "What outputs does the system produce?",
            "constraints": "What constraints must be followed? (language/runtime/performance/security/platform)",
            "non_goals": "What is explicitly out of scope (non-goals)?",
        }
        return prompts[missing_field]

    def normalize_spec(self, draft: SpecDraft) -> SpecDraft:
        return draft


@dataclass
class OpenAIProvider:
    model: str = ""
    max_retries: int = 1
    retry_delay_seconds: float = 0.3

    def __post_init__(self) -> None:
        client_config = resolve_llm_client_config()
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise ProviderError("openai package is required for --use-llm. Install it with `pip install openai`.") from exc
        self._client = OpenAI(**client_config)

    def extract_requirements(self, prompt: str) -> SpecDraft:
        instructions = (
            "Extract required spec fields from the prompt. "
            "Return JSON object with keys: "
            + ", ".join(REQUIRED_FIELDS)
            + ". Each key must map to object: {\"value\": string, \"confidence\": number, \"rationale\": string}. "
            "confidence must be between 0 and 1. No extra keys."
        )
        payload = self._call_json(instructions=instructions, input_text=prompt)
        return self._validate_and_build(payload)

    def generate_followup(self, missing_field: str, draft: SpecDraft) -> str:
        instructions = (
            "Generate one concise follow-up question. "
            "Ask for exactly one missing or ambiguous field. "
            "No preamble. One sentence."
        )
        input_text = json.dumps(
            {
                "target_field": missing_field,
                "existing_fields": draft.as_dict(),
            }
        )
        payload = self._call_json(
            instructions=instructions + " Return JSON: {\"question\": \"...\"}.",
            input_text=input_text,
        )
        question = str(payload.get("question", "")).strip()
        if not question:
            raise ProviderError("LLM follow-up generation returned empty question.")
        return question

    def normalize_spec(self, draft: SpecDraft) -> SpecDraft:
        instructions = (
            "Normalize terminology and wording for consistency. "
            "Do not invent missing facts. "
            "Return same schema used for extraction."
        )
        payload = self._call_json(instructions=instructions, input_text=json.dumps(draft.as_dict()))
        return self._validate_and_build(payload)

    def _call_json(self, instructions: str, input_text: str) -> dict:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.responses.create(
                    model=self.model,
                    instructions=instructions,
                    input=input_text,
                    text={"format": {"type": "json_object"}},
                )
                raw = getattr(response, "output_text", "") or ""
                if not raw:
                    raise ProviderError("LLM returned empty response.")
                return json.loads(raw)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay_seconds)
                    continue
                break
        raise ProviderError(f"LLM request failed after {self.max_retries + 1} attempt(s): {last_error}")

    def _validate_and_build(self, payload: dict) -> SpecDraft:
        if not isinstance(payload, dict):
            raise ProviderError("LLM payload must be a JSON object.")
        normalized: dict[str, dict[str, str | float]] = {}
        for field_name in REQUIRED_FIELDS:
            value = payload.get(field_name)
            if not isinstance(value, dict):
                raise ProviderError(f"LLM payload missing object for field: {field_name}")
            field_value = value.get("value", "")
            confidence = value.get("confidence", 0.0)
            rationale = value.get("rationale", "")
            if not isinstance(field_value, str):
                raise ProviderError(f"Field {field_name}.value must be string.")
            try:
                confidence_num = float(confidence)
            except (TypeError, ValueError) as exc:
                raise ProviderError(f"Field {field_name}.confidence must be number.") from exc
            if confidence_num < 0 or confidence_num > 1:
                raise ProviderError(f"Field {field_name}.confidence out of range [0,1].")
            if not isinstance(rationale, str):
                raise ProviderError(f"Field {field_name}.rationale must be string.")
            normalized[field_name] = {
                "value": field_value.strip(),
                "confidence": confidence_num,
                "rationale": rationale.strip(),
            }
        return SpecDraft.from_dict(normalized)


def resolve_llm_client_config() -> dict:
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        return {
            "api_key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1",
        }

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return {"api_key": openai_key}

    raise ProviderError(
        "Missing API key. Set OPENAI_API_KEY or OPENROUTER_API_KEY when --use-llm is enabled."
    )

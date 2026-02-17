from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Callable, Protocol

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
    is_llm_provider: bool = False

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
    is_llm_provider: bool = True
    model: str = ""
    provider_name: str | None = None
    api_key: str | None = None
    observer: Callable[[dict], None] | None = None
    max_retries: int = 1
    retry_delay_seconds: float = 0.3

    def __post_init__(self) -> None:
        client_config = resolve_llm_client_config(provider_name=self.provider_name, api_key=self.api_key)
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
        payload = self._call_json(stage="parse_prompt", instructions=instructions, input_text=prompt)
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
            stage="generate_followup",
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
        payload = self._call_json(stage="normalize", instructions=instructions, input_text=json.dumps(draft.as_dict()))
        return self._validate_and_build(payload)

    def _call_json(self, stage: str, instructions: str, input_text: str) -> dict:
        normalized_instructions = _ensure_json_keyword(instructions)
        normalized_input = _ensure_json_keyword(input_text)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.time()
            try:
                response = self._client.responses.create(
                    model=self.model,
                    instructions=normalized_instructions,
                    input=normalized_input,
                    text={"format": {"type": "json_object"}},
                )
                raw = getattr(response, "output_text", "") or ""
                if not raw:
                    raise ProviderError("LLM returned empty response.")
                payload = json.loads(raw)
                prompt_tokens, completion_tokens, total_tokens = _extract_usage_tokens(response)
                self._emit_call_event(
                    stage=stage,
                    latency_ms=int((time.time() - started) * 1000),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=_estimate_cost_usd(self.model, prompt_tokens, completion_tokens),
                    retry_count=attempt,
                    schema_valid=True,
                )
                return payload
            except Exception as exc:
                last_error = exc
                if attempt == self.max_retries:
                    self._emit_call_event(
                        stage=stage,
                        latency_ms=int((time.time() - started) * 1000),
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0,
                        estimated_cost_usd=0.0,
                        retry_count=attempt,
                        schema_valid=False,
                    )
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

    def _emit_call_event(
        self,
        stage: str,
        latency_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost_usd: float,
        retry_count: int,
        schema_valid: bool,
    ) -> None:
        if not self.observer:
            return
        self.observer(
            {
                "stage": stage,
                "model": self.model,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(estimated_cost_usd, 8),
                "retry_count": retry_count,
                "schema_valid": schema_valid,
            }
        )


def resolve_llm_client_config(provider_name: str | None = None, api_key: str | None = None) -> dict:
    if provider_name and api_key:
        return _provider_to_client_config(provider_name, api_key)

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


def _provider_to_client_config(provider_name: str, api_key: str) -> dict:
    provider = provider_name.strip().lower()
    key = api_key.strip()
    if not key:
        raise ProviderError("API key is empty.")
    if provider == "openrouter":
        return {"api_key": key, "base_url": "https://openrouter.ai/api/v1"}
    if provider == "openai":
        return {"api_key": key}
    raise ProviderError(f"Unsupported provider: {provider_name}")


def _ensure_json_keyword(text: str) -> str:
    value = (text or "").strip()
    if "json" in value.lower():
        return value
    return f"{value}\nReturn valid json."


def _extract_usage_tokens(response: object) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0, 0
    prompt_tokens = int(getattr(usage, "input_tokens", 0) or getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "output_tokens", 0) or getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens))
    return prompt_tokens, completion_tokens, total_tokens


def _estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing_by_model = {
        "gpt-5-mini": {"input": 0.25, "output": 2.0},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }
    pricing = pricing_by_model.get(model, {"input": 0.0, "output": 0.0})
    return (prompt_tokens / 1_000_000) * pricing["input"] + (completion_tokens / 1_000_000) * pricing["output"]

# SPEC Engine Implementation Plan

## 1. Confirmed Product Decisions
- Provider scope (v1): OpenAI APIs only.
- Confidence policy: model-calibrated thresholds.
- Retry policy: minimal retries for cost control.
- Model tiers: low-cost models for all stages.
- Observability: minimal, cost-focused telemetry only.

## 2. CLI Contract
- Command: `spec-engine generate [options]`
- Options:
  - `--prompt "<text>"`
  - `--output <path>` (default `./SPEC.md`)
  - `--json`
  - `--interactive` (default true)
- Exit codes:
  - `0` success
  - `1` missing required information in non-interactive mode
  - `2` invalid input
  - `3` internal error

## 3. Core Pipeline
1. Parse prompt into candidate values for required fields.
2. Validate required fields and detect ambiguity.
3. Resolve gaps with sequential single-field follow-up questions.
4. Normalize terminology and wording.
5. Generate strict `SPEC.md` or JSON output.

## 4. LLM Integration Design (OpenAI Only)
- Introduce `OpenAIProvider` adapter implementing:
  - `extract_requirements(prompt) -> structured JSON`
  - `generate_followup(missing_field, context) -> question`
  - `normalize_spec(draft) -> normalized draft`
- Use structured response contracts per stage to reduce parser complexity.
- Require schema validation after every model response.
- Use deterministic fallback handling when schema validation fails.

## 5. Model-Calibrated Threshold Strategy
- Each extracted field contains:
  - `value`
  - `confidence` (0.0-1.0)
  - `rationale` (short)
- Initial policy:
  - `confidence >= 0.80`: accepted
  - `0.50 <= confidence < 0.80`: ambiguous -> follow-up question
  - `< 0.50`: missing -> follow-up question
- Calibration loop:
  - Compare confidence with downstream correction rate.
  - Adjust thresholds conservatively after enough runs.

## 6. Minimal Retry Policy
- Retry only for transient/API/validation issues.
- Max retries per stage call: `1`.
- Backoff: fixed short delay (for example 300 ms).
- If retry fails:
  - interactive mode: ask user to rephrase or provide required field directly.
  - non-interactive mode: exit code `3` with actionable error.

## 7. Cost-First Model Tiering
- Use one low-cost primary model for all stages in v1.
- Avoid stage-specific premium models.
- Keep prompts short and stage-specific.
- Enforce max output tokens per stage.
- Track token use and estimated cost per run.

## 8. Minimal, Cost-Focused Observability Spec

### 8.1 Per-Run Required Fields
- `run_id`
- `timestamp`
- `mode` (`interactive` | `non_interactive`)
- `output_path`
- `result` (`success` | `failure`)
- `exit_code`
- `total_tokens`
- `estimated_total_cost_usd`
- `total_latency_ms`

### 8.2 Per-LLM-Call Required Fields
- `run_id`
- `stage` (`parse_prompt` | `generate_followup` | `normalize`)
- `model`
- `latency_ms`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `estimated_cost_usd`
- `retry_count`
- `schema_valid` (boolean)

### 8.3 Data Minimization Rules
- Do not store raw prompt/response text by default.
- Do not store user PII fields intentionally.
- Optional debug mode may store short redacted snippets.

### 8.4 Output Format
- JSONL log file: `.spec-engine/logs/<date>.jsonl`
- One run summary entry + one entry per LLM call.
- Keep stdout summary short and machine-readable.

## 9. Implementation Milestones
1. Foundation:
  - CLI wiring
  - data schema
  - strict markdown renderer
2. LLM integration:
  - OpenAI adapter
  - structured extraction
  - follow-up loop
3. Quality controls:
  - normalization
  - section-order and formatting validators
4. Observability and hardening:
  - JSONL telemetry
  - retry handling
  - exit code completeness

## 10. Test Plan
- Unit tests:
  - requirement validation
  - threshold decisions
  - renderer section ordering
  - retry behavior
- Integration tests:
  - interactive follow-up flow
  - non-interactive missing-field exit code `1`
  - schema-failure path exit code `3`
- Golden tests:
  - deterministic `SPEC.md` output for fixed fixtures

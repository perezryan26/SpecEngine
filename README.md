# Spec Engine

`spec-engine` is a Python CLI that converts a natural-language prompt into a deterministic `SPEC.md` format for coding agents.

## Milestone 1 Status
- CLI wiring
- Core schema and validation
- Deterministic markdown renderer
- Interactive gap filling (non-LLM)

## Milestone 2 Status
- OpenAI provider adapter (`--use-llm`)
- Structured extraction contract (JSON + schema validation)
- Sequential, single-field follow-up generation via provider
- Normalization hook via provider
- Minimal retry policy for LLM calls (1 retry)

## Usage
```bash
spec-engine generate --prompt "Build a CLI tool for CSV validation"
```

```bash
spec-engine generate --prompt "Build a backend API..." --json --output SPEC.json
```

### OpenAI mode
```bash
set OPENAI_API_KEY=your_key_here
spec-engine generate --prompt "Build a CLI for..." --use-llm --model gpt-5-mini
```

### OpenRouter mode
```bash
set OPENROUTER_API_KEY=your_key_here
spec-engine generate --prompt "Build a CLI for..." --use-llm --model openai/gpt-4o-mini
```

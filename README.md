# Spec Engine

`spec-engine` is a Python CLI that converts a natural-language prompt into a deterministic `SPEC.md` format for coding agents.

## Milestone 1 Status
- CLI wiring
- Core schema and validation
- Deterministic markdown renderer
- Interactive gap filling (non-LLM)

## Usage
```bash
spec-engine generate --prompt "Build a CLI tool for CSV validation"
```

```bash
spec-engine generate --prompt "Build a backend API..." --json --output SPEC.json
```


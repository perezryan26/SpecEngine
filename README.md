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

## Main Menu
```bash
spec-engine menu
```

##### Windows

### Interactive Menu based CLI
```bash
python -m spec_engine.cli menu
```

### Non-Interactive CLI 

# Non-LLM mode
```bash
python -m spec_engine.cl generate --prompt "Build a CLI tool for CSV validation"
```

# OpenAI mode
```bash
set OPENAI_API_KEY=your_key_here
python -m spec_engine.cl generate --prompt "Build a CLI for..." --use-llm --model gpt-5-mini
```

# OpenRouter mode
```bash
set OPENROUTER_API_KEY=your_key_here
python -m spec_engine.cl generate --prompt "Build a CLI for..." --use-llm --model openai/gpt-4o-mini
```

Menu flow:
1. `API Keys` to add/modify OpenAI or OpenRouter token.
2. `Generate Spec` asks sequentially:
   - Use an LLM?
   - If yes, select provider and validate key exists
   - Enter prompt
   - Enter output file path
   - Select output representation (JSON/Markdown)

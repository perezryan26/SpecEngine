from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path


class RunLogger:
    def __init__(self, mode: str, output_path: str) -> None:
        self.run_id = str(uuid.uuid4())
        self.mode = mode
        self.output_path = output_path
        self.timestamp = datetime.now(UTC).isoformat()
        self.llm_calls: list[dict] = []

    def log_llm_call(self, payload: dict) -> None:
        self.llm_calls.append({"type": "llm_call", "run_id": self.run_id, **payload})

    def finalize(self, result: str, exit_code: int) -> None:
        total_tokens = sum(int(item.get("total_tokens", 0)) for item in self.llm_calls)
        estimated_total_cost = sum(float(item.get("estimated_cost_usd", 0.0)) for item in self.llm_calls)
        total_latency_ms = sum(int(item.get("latency_ms", 0)) for item in self.llm_calls)

        summary = {
            "type": "run_summary",
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "output_path": self.output_path,
            "result": result,
            "exit_code": exit_code,
            "total_tokens": total_tokens,
            "estimated_total_cost_usd": round(estimated_total_cost, 8),
            "total_latency_ms": total_latency_ms,
        }
        _append_jsonl([summary, *self.llm_calls])


def _append_jsonl(entries: list[dict]) -> None:
    logs_dir = Path(".spec-engine") / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_name = datetime.now(UTC).strftime("%Y-%m-%d") + ".jsonl"
    path = logs_dir / file_name
    with path.open("a", encoding="utf-8") as handle:
        for item in entries:
            handle.write(json.dumps(item) + "\n")


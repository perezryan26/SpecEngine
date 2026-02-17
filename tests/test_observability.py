import json
import os
import tempfile
import unittest
from pathlib import Path

from spec_engine.observability import RunLogger


class ObservabilityTests(unittest.TestCase):
    def test_run_logger_writes_summary_and_calls(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd_before = Path.cwd()
            try:
                os.chdir(td)
                logger = RunLogger(mode="interactive", output_path="./SPEC.md")
                logger.log_llm_call(
                    {
                        "stage": "parse_prompt",
                        "model": "gpt-5-mini",
                        "latency_ms": 12,
                        "prompt_tokens": 100,
                        "completion_tokens": 40,
                        "total_tokens": 140,
                        "estimated_cost_usd": 0.0001,
                        "retry_count": 0,
                        "schema_valid": True,
                    }
                )
                logger.finalize(result="success", exit_code=0)

                logs_dir = Path(".spec-engine") / "logs"
                files = list(logs_dir.glob("*.jsonl"))
                self.assertEqual(len(files), 1)
                lines = files[0].read_text(encoding="utf-8").strip().splitlines()
                self.assertEqual(len(lines), 2)

                summary = json.loads(lines[0])
                call = json.loads(lines[1])
                self.assertEqual(summary["type"], "run_summary")
                self.assertEqual(summary["result"], "success")
                self.assertEqual(summary["exit_code"], 0)
                self.assertEqual(summary["total_tokens"], 140)
                self.assertEqual(call["type"], "llm_call")
                self.assertEqual(call["stage"], "parse_prompt")
            finally:
                os.chdir(cwd_before)


if __name__ == "__main__":
    unittest.main()


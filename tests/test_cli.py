import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        return subprocess.run(
            [sys.executable, "-m", "spec_engine.cli", *args],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_generate_non_interactive_missing_fields_returns_1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "SPEC.md"
            result = self._run("generate", "--prompt", "Build something", "--no-interactive", "--output", str(out))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Missing required information", result.stderr)

    def test_generate_json_success_with_explicit_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "SPEC.json"
            prompt = (
                "Project Name: CSV Guard\n"
                "Project Type: CLI tool\n"
                "Primary Goal: Validate csv files.\n"
                "Target Users: Developers.\n"
                "Inputs: CLI args and file paths.\n"
                "Outputs: Console report.\n"
                "Constraints: Python 3.10+.\n"
                "Non-Goals: No GUI.\n"
            )
            result = self._run("generate", "--prompt", prompt, "--json", "--no-interactive", "--output", str(out))
            self.assertEqual(result.returncode, 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()

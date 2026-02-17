from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import build_spec_draft
from .renderer import render_spec_markdown


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "generate":
        parser.print_help()
        raise SystemExit(2)

    try:
        exit_code = _run_generate(args)
    except Exception as exc:
        sys.stderr.write(f"Internal error: {exc}\n")
        raise SystemExit(3) from exc
    raise SystemExit(exit_code)


def _run_generate(args: argparse.Namespace) -> int:
    prompt = (args.prompt or "").strip()
    if not prompt:
        sys.stderr.write("Invalid input: --prompt is required and must be non-empty.\n")
        return 2

    result = build_spec_draft(prompt=prompt, interactive=args.interactive)

    if not args.interactive and result.missing_fields:
        fields = ", ".join(result.missing_fields)
        sys.stderr.write(f"Missing required information: {fields}\n")
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.json:
        content = json.dumps(result.to_json_dict(), indent=2)
    else:
        content = render_spec_markdown(result.draft)

    output_path.write_text(content + ("" if content.endswith("\n") else "\n"), encoding="utf-8")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spec-engine")
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate")
    generate.add_argument("--prompt", type=str, required=False, help="Initial user prompt")
    generate.add_argument("--output", type=str, default="./SPEC.md", help="Output file path")
    generate.add_argument("--json", action="store_true", help="Output internal representation as JSON")
    generate.add_argument(
        "--interactive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable interactive follow-up for missing fields (default: true)",
    )
    return parser


if __name__ == "__main__":
    main()


from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

from .config_store import get_api_key, set_api_key
from .engine import build_spec_draft
from .providers import OpenAIProvider, ProviderError
from .renderer import render_spec_markdown


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "generate":
            exit_code = _run_generate(args)
        elif args.command == "menu" or args.command is None:
            exit_code = _run_main_menu()
        else:
            parser.print_help()
            exit_code = 2
    except Exception as exc:
        sys.stderr.write(f"Internal error: {exc}\n")
        raise SystemExit(3) from exc
    raise SystemExit(exit_code)


def _run_generate(args: argparse.Namespace) -> int:
    prompt = (args.prompt or "").strip()
    if not prompt:
        sys.stderr.write("Invalid input: --prompt is required and must be non-empty.\n")
        return 2

    try:
        provider = OpenAIProvider(model=args.model) if args.use_llm else None
    except ProviderError as exc:
        sys.stderr.write(f"Internal error: {exc}\n")
        return 3

    result = _generate_spec(
        prompt=prompt,
        output=args.output,
        as_json=args.json,
        interactive=args.interactive,
        provider=provider,
    )
    if isinstance(result, int):
        return result
    return 0


def _generate_spec(prompt: str, output: str, as_json: bool, interactive: bool, provider: OpenAIProvider | None) -> int | None:
    result = build_spec_draft(prompt=prompt, interactive=interactive, provider=provider)

    if not interactive and result.missing_fields:
        fields = ", ".join(result.missing_fields)
        sys.stderr.write(f"Missing required information: {fields}\n")
        return 1

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if as_json:
        content = json.dumps(result.to_json_dict(), indent=2)
    else:
        content = render_spec_markdown(result.draft)

    output_path.write_text(content + ("" if content.endswith("\n") else "\n"), encoding="utf-8")
    return None


def _run_main_menu() -> int:
    while True:
        print("\nMain Menu")
        print("1. API Keys")
        print("2. Generate Spec")
        print("3. Exit")
        choice = input("> ").strip()
        if choice == "1":
            _run_api_keys_menu()
            continue
        if choice == "2":
            return _run_guided_generate()
        if choice == "3":
            return 0
        print("Invalid selection.")


def _run_api_keys_menu() -> None:
    while True:
        print("\nAPI Keys")
        print("1. OpenAI")
        print("2. OpenRouter")
        print("3. Back")
        choice = input("> ").strip()
        if choice == "3":
            return
        provider = ""
        if choice == "1":
            provider = "openai"
        elif choice == "2":
            provider = "openrouter"
        else:
            print("Invalid selection.")
            continue

        token = getpass.getpass(f"Enter {provider} API token: ").strip()
        if not _is_valid_api_key(provider, token):
            print("Invalid API key format.")
            continue
        set_api_key(provider, token)
        print(f"{provider} API token saved.")


def _run_guided_generate() -> int:
    use_llm = _ask_yes_no("Use an LLM? (y/n)")
    provider = None
    if use_llm:
        provider_name = _ask_provider()
        token = get_api_key(provider_name)
        if not _is_valid_api_key(provider_name, token):
            print(f"No valid {provider_name} API key configured. Add it in API Keys menu.")
            return 3
        model = _default_model_for_provider(provider_name)
        try:
            provider = OpenAIProvider(model=model, provider_name=provider_name, api_key=token)
        except ProviderError as exc:
            sys.stderr.write(f"Internal error: {exc}\n")
            return 3

    prompt = input("Enter the prompt:\n> ").strip()
    if not prompt:
        sys.stderr.write("Invalid input: prompt is required.\n")
        return 2

    output_path = input("Enter output file path (default: ./SPEC.md):\n> ").strip() or "./SPEC.md"
    as_json = _ask_output_representation()
    if as_json and output_path == "./SPEC.md":
        output_path = "./SPEC.json"

    result = _generate_spec(
        prompt=prompt,
        output=output_path,
        as_json=as_json,
        interactive=True,
        provider=provider,
    )
    if isinstance(result, int):
        return result
    print(f"Generated: {output_path}")
    return 0


def _ask_yes_no(question: str) -> bool:
    while True:
        value = input(f"{question}\n> ").strip().lower()
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print("Enter y or n.")


def _ask_provider() -> str:
    while True:
        print("Select API key provider")
        print("1. OpenRouter")
        print("2. OpenAI")
        choice = input("> ").strip()
        if choice == "1":
            return "openrouter"
        if choice == "2":
            return "openai"
        print("Invalid selection.")


def _ask_output_representation() -> bool:
    while True:
        print("Select output representation")
        print("1. Markdown")
        print("2. JSON")
        choice = input("> ").strip()
        if choice == "1":
            return False
        if choice == "2":
            return True
        print("Invalid selection.")


def _is_valid_api_key(provider_name: str, api_key: str) -> bool:
    key = api_key.strip()
    if not key:
        return False
    if not key.startswith("sk-"):
        return False
    if provider_name == "openrouter":
        return key.startswith("sk-or-") or key.startswith("sk-")
    if provider_name == "openai":
        return key.startswith("sk-")
    return False


def _default_model_for_provider(provider_name: str) -> str:
    if provider_name == "openrouter":
        return "openai/gpt-4o-mini"
    return "gpt-5-mini"


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
    generate.add_argument(
        "--use-llm",
        action="store_true",
        help="Use OpenAI-based extraction/follow-up/normalization.",
    )
    generate.add_argument(
        "--model",
        type=str,
        default="gpt-5-mini",
        help="OpenAI model name (used only when --use-llm is set).",
    )
    subparsers.add_parser("menu", help="Interactive main menu.")
    return parser


if __name__ == "__main__":
    main()

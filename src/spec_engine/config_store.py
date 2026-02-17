from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_DIR_NAME = ".spec-engine"
CONFIG_FILE_NAME = "config.json"


def config_path(base_dir: Path | None = None) -> Path:
    root = base_dir or Path.cwd()
    return root / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def load_config(base_dir: Path | None = None) -> dict[str, Any]:
    path = config_path(base_dir)
    if not path.exists():
        return {"api_keys": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"api_keys": {}}
    if not isinstance(payload, dict):
        return {"api_keys": {}}
    if "api_keys" not in payload or not isinstance(payload["api_keys"], dict):
        payload["api_keys"] = {}
    return payload


def save_config(config: dict[str, Any], base_dir: Path | None = None) -> None:
    path = config_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def set_api_key(provider_name: str, api_key: str, base_dir: Path | None = None) -> None:
    config = load_config(base_dir)
    config["api_keys"][provider_name] = api_key
    save_config(config, base_dir)


def get_api_key(provider_name: str, base_dir: Path | None = None) -> str:
    config = load_config(base_dir)
    value = config.get("api_keys", {}).get(provider_name, "")
    return value if isinstance(value, str) else ""


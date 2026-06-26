"""Print the current JVM repo registry as JSON.

Run via: python -m swebench.harness.registry_dump
"""
from __future__ import annotations

import importlib
import json
import pkgutil
import sys

import yaml

from swebench.harness import repo_customization as _customization_pkg
from swebench.harness.constants.jvm import MAP_REPO_VERSION_TO_SPECS_JVM


def _build_payload() -> dict:
    from swebench.harness.constants.jvm import _YAML_PATH  # noqa: PLC0415

    yaml_buckets = yaml.safe_load(_YAML_PATH.read_text()) or {}

    payload: dict[str, dict] = {}
    for bucket_name, repos in yaml_buckets.items():
        for repo in repos:
            payload[repo] = {"kind": "bucket", "bucket": bucket_name}

    for info in pkgutil.iter_modules(_customization_pkg.__path__):
        if info.name in {"common"}:
            continue
        module = importlib.import_module(
            f"swebench.harness.repo_customization.{info.name}"
        )
        repo = getattr(module, "REPO", None)
        if repo is None:
            continue
        payload[repo] = {"kind": "customization", "path": module.__file__}

    for repo in payload:
        assert repo in MAP_REPO_VERSION_TO_SPECS_JVM, (
            f"{repo} in registry payload but missing from in-memory map"
        )
    return payload


def main(argv: list[str]) -> int:
    json.dump(_build_payload(), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

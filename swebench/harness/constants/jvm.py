"""JVM (Kotlin + Java Gradle) repo registry.

Reads `jvm_repos.yaml` and merges its bucket assignments with bespoke
customization modules under `repo_customization/`. Customization entries
take precedence over YAML bucket entries.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

import yaml

from swebench.harness import repo_customization as _customization_pkg
from swebench.harness.constants.jvm_base import (
    SPECS_ANDROID_17,
    SPECS_ANDROID_17_X86,
    SPECS_ANDROID_21,
    SPECS_JVM_LIBRARY_17,
    SPECS_JVM_LIBRARY_17_KMP_BROWSER,
    SPECS_JVM_LIBRARY_17_LOW_MEM,
)

_BUCKET_NAME_TO_SPECS = {
    "android_17": SPECS_ANDROID_17,
    "android_17_x86": SPECS_ANDROID_17_X86,
    "android_21": SPECS_ANDROID_21,
    "jvm_library_17": SPECS_JVM_LIBRARY_17,
    "jvm_library_17_kmp_browser": SPECS_JVM_LIBRARY_17_KMP_BROWSER,
    "jvm_library_17_low_mem": SPECS_JVM_LIBRARY_17_LOW_MEM,
}

# YAML lives next to constants/, one level above.
_YAML_PATH = Path(__file__).resolve().parents[1] / "jvm_repos.yaml"


def _load_yaml_buckets() -> dict[str, dict]:
    data = yaml.safe_load(_YAML_PATH.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{_YAML_PATH}: top-level must be a mapping")
    out: dict[str, dict] = {}
    for bucket_name, repos in data.items():
        if bucket_name not in _BUCKET_NAME_TO_SPECS:
            raise ValueError(
                f"{_YAML_PATH}: unknown bucket {bucket_name!r}; "
                f"expected one of {sorted(_BUCKET_NAME_TO_SPECS)}"
            )
        if not isinstance(repos, list):
            raise ValueError(
                f"{_YAML_PATH}: bucket {bucket_name!r} must map to a list of repos"
            )
        specs = _BUCKET_NAME_TO_SPECS[bucket_name]
        for repo in repos:
            out[repo] = specs
    return out


def _discover_customizations() -> dict[str, dict]:
    """Walk repo_customization/ and register each <owner>__<name>.py that
    declares both REPO and SPECS constants.

    Many customization files legitimately omit SPECS — they exist only to
    provide COMMANDS or VERIFICATION_COMMAND overrides (consumed separately
    by repo_customization/__init__.py). Those are silently skipped here.

    A module that has SPECS but no REPO is broken (can't register without a
    slug); warn loudly. A module with neither is almost certainly a stub
    file someone forgot to fill in; warn. ImportErrors already propagate as
    hard failures — no special handling needed.
    """
    out: dict[str, dict] = {}
    for info in pkgutil.iter_modules(_customization_pkg.__path__):
        if info.name in {"common"}:
            continue
        module = importlib.import_module(
            f"swebench.harness.repo_customization.{info.name}"
        )
        repo = getattr(module, "REPO", None)
        specs = getattr(module, "SPECS", None)
        if specs is not None and repo is None:
            print(
                f"jvm.py: repo_customization/{info.name}.py has SPECS but no "
                f"REPO constant — cannot register; fix the file or remove it",
                file=sys.stderr,
            )
            continue
        if specs is None and repo is None:
            print(
                f"jvm.py: repo_customization/{info.name}.py declares neither "
                f"REPO nor SPECS — looks like a stub; fix it or delete it",
                file=sys.stderr,
            )
            continue
        if specs is None:
            # REPO present, SPECS absent — legitimate "extras only" file.
            continue
        out[repo] = specs
    return out


MAP_REPO_VERSION_TO_SPECS_JVM = {
    **_load_yaml_buckets(),
    **_discover_customizations(),  # customization beats YAML
}

MAP_REPO_TO_INSTALL_JVM = {
    repo: f"git clone https://github.com/{repo}.git"
    for repo in MAP_REPO_VERSION_TO_SPECS_JVM.keys()
}

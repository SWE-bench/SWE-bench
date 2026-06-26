"""JVM (Kotlin + Java Gradle) repo registry.

Reads `jvm_repos.yaml` and merges its bucket assignments with bespoke
customization modules under `repo_customization/`. Customization entries
take precedence over YAML bucket entries.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from swebench.harness.constants.jvm_base import (
    SPECS_ANDROID_17,
    SPECS_ANDROID_17_X86,
    SPECS_ANDROID_21,
    SPECS_JVM_LIBRARY_17,
    SPECS_JVM_LIBRARY_17_KMP_BROWSER,
    SPECS_JVM_LIBRARY_17_LOW_MEM,
)
from swebench.harness.repo_customization.InsertKoinIO__koin import (
    SPECS as _SPECS_KOIN,
)
from swebench.harness.repo_customization.JetBrains__Exposed import (
    SPECS as _SPECS_EXPOSED,
)
from swebench.harness.repo_customization.Kotlin__kotlinx_serialization import (
    SPECS as _SPECS_SERIALIZATION,
)
from swebench.harness.repo_customization.ReVanced__revanced_manager import (
    SPECS as _SPECS_REVANCED,
)
from swebench.harness.repo_customization.arrow_kt__arrow import (
    SPECS as _SPECS_ARROW,
)
from swebench.harness.repo_customization.nextcloud__talk_android import (
    SPECS as _SPECS_TALK,
)
from swebench.harness.repo_customization.pinterest__ktlint import (
    SPECS as _SPECS_KTLINT,
)
from swebench.harness.repo_customization.slackhq__circuit import (
    SPECS as _SPECS_CIRCUIT,
)
from swebench.harness.repo_customization.wireapp__wire_android import (
    SPECS as _SPECS_WIRE,
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


MAP_REPO_VERSION_TO_SPECS_JVM = {
    **_load_yaml_buckets(),
    # Bespoke customizations (last wins — override YAML bucket assignment).
    "InsertKoinIO/koin": _SPECS_KOIN,
    "pinterest/ktlint": _SPECS_KTLINT,
    "Kotlin/kotlinx.serialization": _SPECS_SERIALIZATION,
    "JetBrains/Exposed": _SPECS_EXPOSED,
    "slackhq/circuit": _SPECS_CIRCUIT,
    "ReVanced/revanced-manager": _SPECS_REVANCED,
    "arrow-kt/arrow": _SPECS_ARROW,
    "nextcloud/talk-android": _SPECS_TALK,
    "wireapp/wire-android": _SPECS_WIRE,
}

MAP_REPO_TO_INSTALL_JVM = {
    repo: f"git clone https://github.com/{repo}.git"
    for repo in MAP_REPO_VERSION_TO_SPECS_JVM.keys()
}

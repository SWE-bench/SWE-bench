"""Smoke tests: jvm.py loads jvm_repos.yaml correctly."""
from swebench.harness.constants.jvm import MAP_REPO_VERSION_TO_SPECS_JVM
from swebench.harness.constants.jvm_base import (
    SPECS_ANDROID_17,
    SPECS_ANDROID_21,
)


def test_yaml_entries_appear_in_map():
    assert "android/nowinandroid" in MAP_REPO_VERSION_TO_SPECS_JVM
    assert MAP_REPO_VERSION_TO_SPECS_JVM["android/nowinandroid"] is SPECS_ANDROID_17

    assert "DroidKaigi/conference-app-2024" in MAP_REPO_VERSION_TO_SPECS_JVM
    assert (
        MAP_REPO_VERSION_TO_SPECS_JVM["DroidKaigi/conference-app-2024"]
        is SPECS_ANDROID_21
    )


def test_yaml_is_only_source_of_truth():
    import inspect

    from swebench.harness.constants import jvm

    src = inspect.getsource(jvm)
    assert "for repo in [" not in src, (
        "hardcoded bucket assignment block still present in jvm.py"
    )

"""jvm.py auto-discovers customization modules by REPO constant."""
from swebench.harness.constants.jvm import MAP_REPO_VERSION_TO_SPECS_JVM
from swebench.harness.repo_customization.InsertKoinIO__koin import SPECS as KOIN


def test_all_customizations_discovered():
    for slug in [
        "InsertKoinIO/koin",
        "JetBrains/Exposed",
        "Kotlin/kotlinx.serialization",
        "ReVanced/revanced-manager",
        "arrow-kt/arrow",
        "nextcloud/talk-android",
        "pinterest/ktlint",
        "slackhq/circuit",
        "wireapp/wire-android",
    ]:
        assert slug in MAP_REPO_VERSION_TO_SPECS_JVM, (
            f"customization for {slug} not auto-discovered"
        )


def test_customization_beats_yaml():
    # Koin appears in the YAML overlay AS WELL — confirm the customization
    # SPECS (different object) wins.
    assert MAP_REPO_VERSION_TO_SPECS_JVM["InsertKoinIO/koin"] is KOIN


def test_no_explicit_customization_imports_in_jvm():
    import inspect

    from swebench.harness.constants import jvm

    src = inspect.getsource(jvm)
    assert "from swebench.harness.repo_customization." not in src, (
        "jvm.py still has explicit per-repo imports — auto-discovery should "
        "have replaced them"
    )

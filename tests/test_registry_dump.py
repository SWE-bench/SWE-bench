"""registry_dump.py prints the current jvm registry as JSON to stdout."""
import json
import subprocess
import sys


def test_dump_runs_and_prints_known_repos():
    result = subprocess.run(
        [sys.executable, "-m", "swebench.harness.registry_dump"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)

    # YAML-only entry: bucket field only.
    assert payload["android/nowinandroid"] == {"bucket": "android_17"}

    # Customization-backed override (Koin's customization declares SPECS).
    koin = payload["InsertKoinIO/koin"]
    assert koin["customization_path"].endswith("InsertKoinIO__koin.py")

    # LibChecker: YAML bucket + extras-only customization file — both fields present.
    lib = payload["LibChecker/LibChecker"]
    assert lib["bucket"] == "android_17"
    assert lib["customization_path"].endswith("LibChecker__LibChecker.py")

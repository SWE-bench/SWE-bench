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

    assert payload["android/nowinandroid"] == {
        "kind": "bucket",
        "bucket": "android_17",
    }

    koin = payload["InsertKoinIO/koin"]
    assert koin["kind"] == "customization"
    assert koin["path"].endswith("InsertKoinIO__koin.py")

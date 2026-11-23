"""Issue #728: a model patch must not be able to xfail the target test.

The eval script resets the test files, but pytest's own configuration survives
the model patch. A patch that adds ``addopts = "-p plugin"`` to the repo's
``pyproject.toml`` (or ``pytest.ini``, ``setup.cfg``, ``tox.ini``, a
``conftest.py``) alongside a plugin that marks the FAIL_TO_PASS test xfail turns
a genuine failure into a consistent ``XFAIL`` log with exit code 0, which grades
as resolved.

This builds the eval script the harness would run and executes it against a
minimal repo: the log must show the real failure, not the injected xfail.
"""

import subprocess
import sys
from pathlib import Path

from swebench.harness.constants import FAIL_TO_PASS, PASS_TO_PASS
from swebench.harness.grading import (
    get_eval_tests_report,
    get_logs_eval,
    get_resolution_status,
)
from swebench.harness.utils import make_test_spec

TARGET = "tests/test_calc.py::test_add"

EVAL_SCRIPT = """#!/bin/bash
set -uxo pipefail
cd {repo}
git apply -v - <<'EOF'
diff --git a/tests/test_new.py b/tests/test_new.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/tests/test_new.py
@@ -0,0 +1,2 @@
+def test_new():
+    pass
EOF
: '>>>>> Start Test Output'
{py} -m pytest -rA
: '>>>>> End Test Output'
"""


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _exploited_repo(tmp_path: Path) -> Path:
    """Base commit, then the model patch: a config-driven xfail plugin."""
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n")
    (repo / "tests" / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    )
    (repo / "pyproject.toml").write_text("[project]\nname = 'calc'\nversion = '0'\n")
    _git(repo, "init", "-q", ".")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "base")

    # The bug is left in place; only pytest's configuration is changed.
    (repo / "pyproject.toml").write_text(
        "[project]\nname = 'calc'\nversion = '0'\n\n"
        '[tool.pytest.ini_options]\naddopts = "-p custom_plugin"\n'
    )
    (repo / "custom_plugin.py").write_text(
        "import pytest\n"
        f"TARGET = {TARGET!r}\n"
        "def pytest_collection_modifyitems(config, items):\n"
        "    for item in items:\n"
        "        if item.nodeid == TARGET:\n"
        "            item.add_marker(pytest.mark.xfail)\n"
    )
    return repo


def test_a_config_driven_xfail_does_not_resolve_the_instance(tmp_path):
    repo = _exploited_repo(tmp_path)
    spec = make_test_spec(
        {
            "instance_id": "x__x-1",
            "image": "img",
            "repo": "x/x",
            "version": "1.0",
            "FAIL_TO_PASS": f'["{TARGET}"]',
            "PASS_TO_PASS": "[]",
            "log_parser": "parse_log_pytest",
            "eval_type": "pass_and_fail",
            "eval_script": EVAL_SCRIPT.format(repo=repo, py=sys.executable),
        }
    )
    script = tmp_path / "eval.sh"
    script.write_text(spec.eval_script)

    proc = subprocess.run(
        ["bash", str(script)], capture_output=True, text=True, check=False
    )
    log = tmp_path / "test_output.txt"
    log.write_text(proc.stdout + proc.stderr)

    status_map, found = get_logs_eval(spec, str(log))
    assert found
    report = get_eval_tests_report(
        status_map, {FAIL_TO_PASS: [TARGET], PASS_TO_PASS: []}
    )
    assert get_resolution_status(report) == "RESOLVED_NO", status_map

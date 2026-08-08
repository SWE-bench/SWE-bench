from swebench.harness.constants import TestStatus as _TestStatus
from swebench.harness.grading import get_logs_eval
from swebench.harness.modal_eval.utils import prepare_modal_eval_script
from swebench.harness.test_spec.test_spec import (
    EVAL_SCRIPT_STRICT_MODE_HEADER,
    TestSpec as _TestSpec,
)


def make_test_spec(repo="pvlib/pvlib-python", version="0.1"):
    return _TestSpec(
        instance_id="test-instance",
        repo=repo,
        version=version,
        repo_script_list=[],
        eval_script_list=[],
        env_script_list=[],
        arch="x86_64",
        FAIL_TO_PASS=[],
        PASS_TO_PASS=[],
        language="py",
        docker_specs={},
        namespace=None,
    )


def test_eval_script_starts_with_bash_strict_mode():
    assert make_test_spec().eval_script.startswith(
        f"#!/bin/bash\n{EVAL_SCRIPT_STRICT_MODE_HEADER}\n"
    )


def test_prepare_modal_eval_script_routes_xtrace_to_stdout():
    prepared = prepare_modal_eval_script(
        f"#!/bin/bash\n{EVAL_SCRIPT_STRICT_MODE_HEADER}\necho hi\n"
    )
    assert prepared.startswith(
        f"#!/bin/bash\nBASH_XTRACEFD=1\n{EVAL_SCRIPT_STRICT_MODE_HEADER}\n"
    )
    assert "exec 2>&1" not in prepared
    assert prepared.count("BASH_XTRACEFD=1\n") == 1


def test_prepare_modal_eval_script_on_real_eval_script():
    prepared = prepare_modal_eval_script(make_test_spec().eval_script)
    assert prepared.startswith(
        f"#!/bin/bash\nBASH_XTRACEFD=1\n{EVAL_SCRIPT_STRICT_MODE_HEADER}\n"
    )


def test_prepare_modal_eval_script_is_idempotent():
    once = prepare_modal_eval_script(make_test_spec().eval_script)
    twice = prepare_modal_eval_script(once)
    assert once == twice
    assert twice.count("BASH_XTRACEFD=1\n") == 1


def test_get_logs_eval_parses_fixed_modal_output(tmp_path):
    log_path = tmp_path / "test_output.txt"
    log_path.write_text(
        "+ git checkout abc123 tests/test_example.py\n"
        "+ : '>>>>> Start Test Output'\n"
        "+ pytest -rA\n"
        "PASSED tests/test_example.py::test_ok\n"
        "+ : '>>>>> End Test Output'\n"
        "+ git checkout abc123 tests/test_example.py\n"
    )

    status_map, found = get_logs_eval(make_test_spec(), str(log_path))

    assert found is True
    assert status_map == {"tests/test_example.py::test_ok": _TestStatus.PASSED.value}

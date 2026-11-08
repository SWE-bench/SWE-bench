"""A suite-level failure that names no spec must not grade as resolved (#686).

`parse_log_marked` records numbered Jasmine failures only, and `check_fail_only`
assumes any test absent from the status map passed. A real `afterAll` exception
produces a "Suite error" block plus "1 spec, 1 failure" and exit code 1, but no
numbered failure: the map is empty, `SUITE_RAN` matches (so the run is not
discarded as resultless), and every FAIL_TO_PASS case scores as a success.

A non-zero exit with nothing recorded means the run is not evaluable, whichever
parser produced the map.
"""

from swebench.harness.constants import END_TEST_OUTPUT, START_TEST_OUTPUT
from swebench.harness.grading import get_logs_eval
from swebench.types import TestSpec

JASMINE_SUITE_ERROR = """\
Started
.

Suite error: evaluation reproduction
  Message:
    Error: suite teardown failed
  Stack:
    Error: suite teardown failed
        at <Jasmine>
1 spec, 1 failure
"""

JASMINE_CLEAN = """\
Started
.

1 spec, 0 failures
"""


def _spec():
    return TestSpec(
        instance_id="synthetic-jasmine-1",
        image="unused",
        eval_script_list=[],
        repo="markedjs/marked",
        version="synthetic",
        FAIL_TO_PASS=["evaluation reproduction required regression test"],
        PASS_TO_PASS=[],
        log_parser="parse_log_marked",
        eval_type="fail_only",
    )


def _log(tmp_path, body, exit_code):
    log = tmp_path / "test_output.txt"
    log.write_text(
        f"{START_TEST_OUTPUT}\n{body}\n{END_TEST_OUTPUT}\n"
        f">>>>> Test Exit Code: {exit_code}\n"
    )
    return str(log)


def test_suite_level_failure_is_not_graded(tmp_path):
    status_map, found = get_logs_eval(_spec(), _log(tmp_path, JASMINE_SUITE_ERROR, 1))
    assert (status_map, found) == ({}, False)


def test_clean_jasmine_run_is_still_graded(tmp_path):
    status_map, found = get_logs_eval(_spec(), _log(tmp_path, JASMINE_CLEAN, 0))
    assert found and status_map == {}

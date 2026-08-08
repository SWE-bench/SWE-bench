import pytest

from swebench.harness.constants import (
    FAIL_TO_PASS,
    PASS_TO_PASS,
    ResolvedStatus,
    TestStatus as _TestStatus,
)
from swebench.harness.grading import get_eval_tests_report, get_resolution_status
from swebench.harness.log_parsers.python import (
    parse_log_pytest,
    parse_log_pytest_options,
    parse_log_pytest_v2,
)


PYLINT_6528_SKIPPED_TESTS = [
    "tests/lint/unittest_lint.py::test_custom_should_analyze_file",
    "tests/lint/unittest_lint.py::test_multiprocessing[1]",
    "tests/lint/unittest_lint.py::test_multiprocessing[2]",
    "tests/test_self.py::TestRunTC::test_jobs_score",
]


def test_parse_pytest_skipped_verbose_nodeid() -> None:
    log = "\n".join(
        [
            "tests/lint/unittest_lint.py::LintRunTC::test_jobs_option SKIPPED [1] Need 2 or more cores",
            "SKIPPED [1] tests/lint/unittest_lint.py:774: Need 2 or more cores",
        ]
    )

    result = parse_log_pytest_options(log, None)

    assert result == {
        "tests/lint/unittest_lint.py::LintRunTC::test_jobs_option": (
            _TestStatus.SKIPPED.value
        )
    }


def test_parse_pytest_skipped_summary_without_nodeid_is_ignored() -> None:
    log = "SKIPPED [1] tests/lint/unittest_lint.py:774: Need 2 or more cores"

    assert parse_log_pytest_options(log, None) == {}


@pytest.mark.parametrize(
    "parser", [parse_log_pytest, parse_log_pytest_options, parse_log_pytest_v2]
)
def test_parse_pytest_supports_status_before_and_after_nodeid(parser) -> None:
    log = "\n".join(
        [
            "PASSED tests/test_widget.py::test_create",
            "tests/test_widget.py::test_delete FAILED [100%]",
        ]
    )

    assert parser(log, None) == {
        "tests/test_widget.py::test_create": _TestStatus.PASSED.value,
        "tests/test_widget.py::test_delete": _TestStatus.FAILED.value,
    }


def test_pylint_6528_single_core_skips_do_not_cause_false_regression() -> None:
    fail_to_pass = [
        "tests/lint/unittest_lint.py::test_recursive_ignore[--ignore-ignored_subdirectory]",
        "tests/lint/unittest_lint.py::test_recursive_ignore[--ignore-patterns-ignored_*]",
        "tests/test_self.py::TestRunTC::test_ignore_recursive",
        "tests/test_self.py::TestRunTC::test_ignore_pattern_recursive",
    ]
    log = "\n".join(
        [
            *(f"{test} PASSED" for test in fail_to_pass),
            f"{PYLINT_6528_SKIPPED_TESTS[0]} SKIPPED [1] Need 2 or more cores",
            f"{PYLINT_6528_SKIPPED_TESTS[1]} SKIPPED [1] Need 2 or more cores",
            f"{PYLINT_6528_SKIPPED_TESTS[2]} SKIPPED [1] Need 2 or more cores",
            f"{PYLINT_6528_SKIPPED_TESTS[3]} SKIPPED [1] Need 2 or more cores",
            "SKIPPED [1] tests/lint/unittest_lint.py:774: Need 2 or more cores",
            "SKIPPED [2] tests/lint/unittest_lint.py:803: Need 2 or more cores",
            "SKIPPED [1] tests/test_self.py:1050: Need 2 or more cores",
            "2 failed, 171 passed, 4 skipped, 1 xfailed",
        ]
    )

    status_map = parse_log_pytest_options(log, None)
    report = get_eval_tests_report(
        status_map,
        {FAIL_TO_PASS: fail_to_pass, PASS_TO_PASS: PYLINT_6528_SKIPPED_TESTS},
    )

    assert all(
        status_map[test] == _TestStatus.SKIPPED.value
        for test in PYLINT_6528_SKIPPED_TESTS
    )
    assert "[1]" not in status_map
    assert "[2]" not in status_map
    assert get_resolution_status(report) == ResolvedStatus.FULL.value

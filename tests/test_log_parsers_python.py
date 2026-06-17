from swebench.harness.constants import TestStatus
from swebench.harness.log_parsers.python import parse_log_pytest_options


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
            TestStatus.SKIPPED.value
        )
    }


def test_parse_pytest_skipped_summary_without_nodeid_is_ignored() -> None:
    log = "SKIPPED [1] tests/lint/unittest_lint.py:774: Need 2 or more cores"

    assert parse_log_pytest_options(log, None) == {}

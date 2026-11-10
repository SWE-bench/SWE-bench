from swebench.harness.log_parsers.python import (
    parse_log_matplotlib,
    parse_log_pytest,
    parse_log_pytest_options,
    parse_log_pytest_v2,
    parse_log_seaborn,
)
from swebench.harness.constants import TestStatus


class TestPytestParsersPreserveFailed:
    """Verify that a later PASSED line does not overwrite FAILED/ERROR (#708)."""

    def test_pytest_parsers_preserve_failed_against_later_passed(self):
        log = """\
FAILED test_pkg/tests/test_foo.py::test_bar - assert 0
FAILED test_pkg/tests/test_foo.py::test_baz - assert 0
=== 2 failed in 0.01s ===
PASSED test_pkg/tests/test_foo.py::test_bar
"""
        for parser in (
            parse_log_pytest,
            parse_log_pytest_options,
            parse_log_pytest_v2,
            parse_log_matplotlib,
        ):
            res = parser(log, None)
            assert res.get("test_pkg/tests/test_foo.py::test_bar") == TestStatus.FAILED.value, parser.__name__
            assert res.get("test_pkg/tests/test_foo.py::test_baz") == TestStatus.FAILED.value, parser.__name__

    def test_pytest_parsers_preserve_error_against_later_passed(self):
        log = """\
ERROR test_pkg/tests/test_foo.py::test_bar
PASSED test_pkg/tests/test_foo.py::test_bar
"""
        for parser in (
            parse_log_pytest,
            parse_log_pytest_options,
            parse_log_pytest_v2,
            parse_log_matplotlib,
        ):
            res = parser(log, None)
            assert res.get("test_pkg/tests/test_foo.py::test_bar") == TestStatus.ERROR.value, parser.__name__

    def test_wrapped_progress_artifact_can_still_become_passed(self):
        """Pass-to-pass backward compatibility for pytest-dev suite with [100%]."""
        log = """\
FAILED [100%]
PASSED [100%]
"""
        res = parse_log_pytest(log, None)
        assert res.get("[100%]") == TestStatus.PASSED.value

    def test_pytest_short_summary_excludes_printed_statuses(self):
        log = """\
============================= test session starts ==============================
=================================== FAILURES ===================================
----------------------------- Captured stdout call -----------------------------
PASSED test_example.py::test_never_runs
=========================== short test summary info ============================
FAILED test_example.py::test_first - assert False
PASSED test_example.py::test_finished
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
PASSED test_example.py::test_after_summary
========================= 1 failed, 1 passed in 0.01s ==========================
""".replace("short test summary info", "\x1b[1mshort test summary info\x1b[0m")
        for parser in (
            parse_log_pytest,
            parse_log_pytest_options,
            parse_log_pytest_v2,
            parse_log_matplotlib,
            parse_log_seaborn,
        ):
            assert parser(log, None) == {
                "test_example.py::test_first": TestStatus.FAILED.value,
                "test_example.py::test_finished": TestStatus.PASSED.value,
            }, parser.__name__

    def test_pytest_short_summary_preserves_legacy_output(self):
        log = """\
============================= test session starts ==============================
PASSED test_example.py::test_legacy
============================= test session starts ==============================
PASSED [100%]
=========================== short test summary info ============================
PASSED test_example.py::test_finished
============================== 1 passed in 0.01s ===============================
"""
        assert parse_log_pytest(log, None) == {
            "test_example.py::test_legacy": TestStatus.PASSED.value,
            "[100%]": TestStatus.PASSED.value,
            "test_example.py::test_finished": TestStatus.PASSED.value,
        }

    def test_partial_pytest_short_summary_preserves_verbose_results(self):
        for parser, progress in (
            (parse_log_pytest_v2, "test_example.py::test_finished PASSED"),
            (parse_log_seaborn, "test_example.py::test_finished PASSED [ 50%]"),
        ):
            log = f"""\
{progress}
=================================== FAILURES ===================================
----------------------------- Captured stdout call -----------------------------
test_example.py::test_never_runs PASSED [100%]
=========================== short test summary info ============================
FAILED test_example.py::test_first - assert False
========================= 1 failed, 1 passed in 0.01s ==========================
"""
            assert parser(log, None) == {
                "test_example.py::test_finished": TestStatus.PASSED.value,
                "test_example.py::test_first": TestStatus.FAILED.value,
            }, parser.__name__


class TestParseLogSeaborn:
    """Tests for parse_log_seaborn used by mwaskom/seaborn."""

    def test_parse_pass_and_fail(self):
        """Test parsing the three supported line formats."""
        log = """\
test_a.py::test_one PASSED [ 50%]
PASSED test_b.py::test_two
FAILED test_c.py::test_three
"""
        result = parse_log_seaborn(log, test_spec=None)

        assert result == {
            "test_a.py::test_one": TestStatus.PASSED.value,
            "test_b.py::test_two": TestStatus.PASSED.value,
            "test_c.py::test_three": TestStatus.FAILED.value,
        }

    def test_bare_status_lines_do_not_crash(self):
        """Status words on their own line (e.g. interleaved/captured output)
        must be ignored rather than raising IndexError."""
        log = """\
test_a.py::test_one PASSED [ 50%]
PASSED
FAILED
 PASSED
test_b.py::test_two PASSED [100%]
"""
        result = parse_log_seaborn(log, test_spec=None)

        assert result == {
            "test_a.py::test_one": TestStatus.PASSED.value,
            "test_b.py::test_two": TestStatus.PASSED.value,
        }

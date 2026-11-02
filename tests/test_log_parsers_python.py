import pytest

from swebench.harness.log_parsers.python import parse_log_django, parse_log_seaborn
from swebench.harness.constants import TestStatus


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


class TestParseLogDjango:
    """Tests for parse_log_django used by the django/django instances."""

    def test_parse_pass_fail_and_error(self):
        """The normal unittest output formats still parse unchanged."""
        log = """\
test_one (app.tests.MyTest) ... ok
test_two (app.tests.MyTest) ... FAIL
test_three (app.tests.MyTest) ... skipped 'no reason'
ERROR: test_four (app.tests.MyTest)
"""
        result = parse_log_django(log, test_spec=None)

        assert result == {
            "test_one (app.tests.MyTest)": TestStatus.PASSED.value,
            "test_two (app.tests.MyTest)": TestStatus.FAILED.value,
            "test_three (app.tests.MyTest)": TestStatus.SKIPPED.value,
            "test_four": TestStatus.ERROR.value,
        }

    @pytest.mark.parametrize("bare", ["FAIL:", "ERROR:", "FAIL:   ", "  ERROR:  "])
    def test_bare_status_lines_do_not_crash(self, bare: str):
        """A status prefix with no test name after it must be ignored, not raise IndexError.

        Lines are stripped before this check, so trailing whitespace is no protection.
        """
        log = f"test_one (app.tests.MyTest) ... ok\n{bare}\ntest_two (app.tests.MyTest) ... ok\n"

        result = parse_log_django(log, test_spec=None)

        assert result == {
            "test_one (app.tests.MyTest)": TestStatus.PASSED.value,
            "test_two (app.tests.MyTest)": TestStatus.PASSED.value,
        }

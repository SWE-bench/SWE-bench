from swebench.harness.log_parsers.python import parse_log_seaborn
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

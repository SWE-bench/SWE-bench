from swebench.harness.log_parsers.java import parse_log_gradle_custom
from swebench.harness.constants import TestStatus


class TestParseLogGradleCustom:
    """Tests for parse_log_gradle_custom used by Apache Lucene and RxJava."""

    def test_parse_pass_and_fail(self):
        """Test parsing normal output with passing and failing tests."""
        log = """com.example.Test > testOne PASSED
com.example.Test > testTwo FAILED
"""
        result = parse_log_gradle_custom(log, test_spec=None)

        assert len(result) == 2
        assert result["com.example.Test > testOne"] == TestStatus.PASSED.value
        assert result["com.example.Test > testTwo"] == TestStatus.FAILED.value

    def test_ignores_non_test_lines(self):
        """Test that task lines and other noise are ignored."""
        log = """> Task :test
WARNING: Some warning
com.example.Test > testMethod PASSED
BUILD SUCCESSFUL
"""
        result = parse_log_gradle_custom(log, test_spec=None)

        assert result == {"com.example.Test > testMethod": TestStatus.PASSED.value}

    def test_interleaved_logs_race_condition(self):
        """Test parsing when warnings split test name from status."""
        log = """com.example.Test > testOne PASSED
com.example.Test > testTwo
WARNING: interleaved output
PASSED
com.example.Test > testThree
FAILED
"""
        result = parse_log_gradle_custom(log, test_spec=None)

        assert len(result) == 3
        assert result["com.example.Test > testOne"] == TestStatus.PASSED.value
        assert result["com.example.Test > testTwo"] == TestStatus.PASSED.value
        assert result["com.example.Test > testThree"] == TestStatus.FAILED.value

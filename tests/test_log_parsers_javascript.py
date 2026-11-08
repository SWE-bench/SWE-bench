from swebench.harness.log_parsers.javascript import parse_log_jest, parse_log_karma
from swebench.harness.constants import TestStatus


class TestParseLogJest:
    """Tests for parse_log_jest used by Jest-based JS/TS repos."""

    def test_parse_pass_and_fail(self):
        """Test parsing normal verbose Jest output."""
        log = """✓ adds two numbers (2 ms)
✕ subtracts two numbers
○ skipped test
"""
        result = parse_log_jest(log, test_spec=None)

        assert len(result) == 3
        assert result["adds two numbers"] == TestStatus.PASSED.value
        assert result["subtracts two numbers"] == TestStatus.FAILED.value
        assert result["skipped test"] == TestStatus.SKIPPED.value

    def test_same_test_name_stable_with_and_without_duration(self):
        """Jest only prints a "(N ms)" duration suffix above a small timing threshold,
        so the same test can appear with or without it across runs. The captured test
        name must be identical either way, otherwise it silently maps to two different
        dict keys and a real fail->pass transition can be missed."""
        with_duration = "✓ builds the correct query (105 ms)"
        without_duration = "✓ builds the correct query"

        result_with = parse_log_jest(with_duration, test_spec=None)
        result_without = parse_log_jest(without_duration, test_spec=None)

        assert list(result_with.keys()) == ["builds the correct query"]
        assert list(result_with.keys()) == list(result_without.keys())

    def test_strips_leading_and_trailing_whitespace(self):
        """Indentation from nested describe blocks shouldn't leak into the test name."""
        log = "    ✓ works when nested (3 ms)"
        result = parse_log_jest(log, test_spec=None)

        assert result == {"works when nested": TestStatus.PASSED.value}


class TestParseLogKarma:
    """Tests for parse_log_karma used by Karma-based JS/TS repos."""

    def test_sibling_suites_at_same_indentation_replace_previous_suite(self):
        """Sibling describe blocks at the same indentation level must replace
        the previous sibling rather than keeping the previous sibling's name."""
        log = """Starting browser HeadlessChrome
  Suite A
    ✔ test 1
  Suite B
    ✔ test 1
    ✖ test 2
SUMMARY:
"""
        result = parse_log_karma(log, test_spec=None)

        assert result == {
            "Suite A > test 1": TestStatus.PASSED.value,
            "Suite B > test 1": TestStatus.PASSED.value,
            "Suite B > test 2": TestStatus.FAILED.value,
        }

    def test_nested_and_dedented_suites_unwind_full_hierarchy(self):
        """Exiting a deeply nested describe block into an outer sibling describe
        block must pop all deeper levels as well as the previous sibling at the
        new indentation level, and push the new suite name."""
        log = """Starting browser HeadlessChrome
  Outer A
    Inner A1
      Deep A1a
        ✔ deep test
    Inner A2
      ✔ inner 2 test
  Outer B
    ✔ outer B test
SUMMARY:
"""
        result = parse_log_karma(log, test_spec=None)

        assert result == {
            "Outer A > Inner A1 > Deep A1a > deep test": TestStatus.PASSED.value,
            "Outer A > Inner A2 > inner 2 test": TestStatus.PASSED.value,
            "Outer B > outer B test": TestStatus.PASSED.value,
        }


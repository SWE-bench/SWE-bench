from swebench.harness.constants import TestStatus
from swebench.harness.log_parsers.ruby import parse_log_minitest

NAME = "TestFilters#test_: filters where_exp filter should filter objects"


class TestParseLogMinitest:
    """Tests for parse_log_minitest (minitest -v), used by jekyll/jekyll."""

    def test_result_codes(self):
        log = "\n".join(
            [
                f"{NAME} a.  = 0.01 s = .",
                f"{NAME} b.  = 0.00 s = F",
                f"{NAME} c.  = 1.25 s = E",
            ]
        )
        assert parse_log_minitest(log, None) == {
            f"{NAME} a": TestStatus.PASSED.value,
            f"{NAME} b": TestStatus.FAILED.value,
            f"{NAME} c": TestStatus.FAILED.value,
        }

    def test_skip_is_not_a_pass(self):
        # "S" has no "." after the last "="; the parser must not fall back to the
        # decimal point of the duration
        log = f"{NAME}.  = 0.00 s = S\n"
        assert parse_log_minitest(log, None) == {NAME: TestStatus.SKIPPED.value}

    def test_ignores_summary_lines(self):
        log = (
            "Finished in 0.040000s, 300.0000 runs/s, 275.0000 assertions/s.\n"
            "12 runs, 11 assertions, 0 failures, 0 errors, 1 skips\n"
        )
        assert parse_log_minitest(log, None) == {}

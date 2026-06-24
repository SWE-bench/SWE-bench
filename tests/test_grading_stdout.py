from swebench.harness.constants import (
    END_TEST_OUTPUT,
    START_TEST_OUTPUT,
    TEST_EXIT_CODE_PREFIX,
)
from swebench.harness.grading import _detect_stdout_tampering, _parse_test_exit_code


def test_parse_test_exit_code() -> None:
    content = f"""{START_TEST_OUTPUT}
=== 1 passed in 0.10 seconds ===
{END_TEST_OUTPUT}
{TEST_EXIT_CODE_PREFIX}0
"""
    assert _parse_test_exit_code(content) == 0


def test_detect_stdout_tampering() -> None:
    spoofed = "import sys\nclass SpoofedStdout:\n    pass\nsys.stdout = SpoofedStdout()"
    assert _detect_stdout_tampering(spoofed) is True
    assert _detect_stdout_tampering("=== 1 passed in 0.10 seconds ===") is False

from swebench.harness.constants import FAIL_TO_PASS, PASS_TO_PASS, TestStatus
from swebench.harness.grading import get_eval_tests_report


def test_skipped_pass_to_pass_tests_are_maintained() -> None:
    report = get_eval_tests_report(
        {
            "test_fix": TestStatus.SKIPPED.value,
            "test_maintenance": TestStatus.SKIPPED.value,
        },
        {
            FAIL_TO_PASS: ["test_fix"],
            PASS_TO_PASS: ["test_maintenance"],
        },
    )

    assert report[FAIL_TO_PASS]["failure"] == ["test_fix"]
    assert report[PASS_TO_PASS]["success"] == ["test_maintenance"]
    assert report[PASS_TO_PASS]["failure"] == []

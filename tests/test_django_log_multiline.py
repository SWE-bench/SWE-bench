from swebench.harness.constants import TestStatus
from swebench.harness.log_parsers.python import parse_log_django


def test_django_ignores_stray_ok_without_overwriting_reported_results():
    log = """\
test_failed (app.Test) ... FAIL
okay unrelated output
test_error (app.Test) ... ERROR
ok
test_skipped (app.Test) ... skipped 'unavailable'
ok
test_pending (app.Test) ... Django system checks
okay still not finished
test_multiline (app.Test) ... more Django output
ok
"""
    assert parse_log_django(log, test_spec=None) == {
        "test_failed (app.Test)": TestStatus.FAILED.value,
        "test_error (app.Test)": TestStatus.ERROR.value,
        "test_skipped (app.Test)": TestStatus.SKIPPED.value,
        "test_multiline (app.Test)": TestStatus.PASSED.value,
    }

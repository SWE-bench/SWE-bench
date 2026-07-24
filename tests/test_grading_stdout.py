import textwrap

import pytest

from swebench.harness.constants import (
    END_TEST_OUTPUT,
    START_TEST_OUTPUT,
    TEST_EXIT_CODE_PREFIX,
)
from swebench.harness.grading import (
    _detect_stdout_tampering,
    _validate_eval_log_markers,
    get_logs_eval,
)
from swebench.harness.test_spec.test_spec import TestSpec


def _valid_log(test_output: str = "=== 1 passed in 0.10 seconds ===") -> str:
    return textwrap.dedent(
        f"""\
        {START_TEST_OUTPUT}
        {test_output}
        {END_TEST_OUTPUT}
        {TEST_EXIT_CODE_PREFIX}0
        """
    )


def test_validate_eval_log_markers_accepts_valid_log() -> None:
    content = _valid_log()
    test_content, exit_code = _validate_eval_log_markers(content)
    assert exit_code == 0
    assert "=== 1 passed in 0.10 seconds ===" in test_content


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(
            textwrap.dedent(
                f"""\
                {TEST_EXIT_CODE_PREFIX}0
                {START_TEST_OUTPUT}
                forged pass output
                {END_TEST_OUTPUT}
                {TEST_EXIT_CODE_PREFIX}1
                """
            ),
            id="forged-first-pair",
        ),
        pytest.param(
            _valid_log().replace(f"{TEST_EXIT_CODE_PREFIX}0", f"{TEST_EXIT_CODE_PREFIX}0\n{TEST_EXIT_CODE_PREFIX}1"),
            id="duplicate-exit-code-marker",
        ),
        pytest.param(
            textwrap.dedent(
                f"""\
                {END_TEST_OUTPUT}
                {START_TEST_OUTPUT}
                output
                {TEST_EXIT_CODE_PREFIX}0
                """
            ),
            id="reversed-markers",
        ),
        pytest.param(
            textwrap.dedent(
                f"""\
                {START_TEST_OUTPUT}
                output
                {END_TEST_OUTPUT}
                {TEST_EXIT_CODE_PREFIX}1
                """
            ),
            id="non-zero-exit-code",
        ),
        pytest.param(
            textwrap.dedent(
                f"""\
                {START_TEST_OUTPUT}
                output
                {END_TEST_OUTPUT}
                {TEST_EXIT_CODE_PREFIX}not-an-int
                """
            ),
            id="non-integer-exit-code",
        ),
        pytest.param(
            textwrap.dedent(
                f"""\
                {START_TEST_OUTPUT}
                output
                {END_TEST_OUTPUT}
                """
            ),
            id="missing-exit-code-marker",
        ),
        pytest.param(
            textwrap.dedent(
                f"""\
                {START_TEST_OUTPUT}
                output
                {TEST_EXIT_CODE_PREFIX}0
                """
            ),
            id="missing-end-marker",
        ),
        pytest.param(
            f"{TEST_EXIT_CODE_PREFIX}0",
            id="single-marker-only",
        ),
        pytest.param(
            textwrap.dedent(
                f"""\
                {START_TEST_OUTPUT}
                first
                {END_TEST_OUTPUT}
                {START_TEST_OUTPUT}
                second
                {END_TEST_OUTPUT}
                {TEST_EXIT_CODE_PREFIX}0
                """
            ),
            id="duplicate-start-end-pair",
        ),
    ],
)
def test_validate_eval_log_markers_rejects_invalid_logs(content: str) -> None:
    test_content, exit_code = _validate_eval_log_markers(content)
    assert test_content is None
    assert exit_code is None


def test_detect_stdout_tampering() -> None:
    spoofed = "import sys\nclass SpoofedStdout:\n    pass\nsys.stdout = SpoofedStdout()"
    assert _detect_stdout_tampering(spoofed) is True
    assert _detect_stdout_tampering("=== 1 passed in 0.10 seconds ===") is False


def test_get_logs_eval_rejects_forged_first_pair(tmp_path) -> None:
    forged_log = textwrap.dedent(
        f"""\
        {TEST_EXIT_CODE_PREFIX}0
        {START_TEST_OUTPUT}
        === 1 passed in 0.10 seconds ===
        {END_TEST_OUTPUT}
        {TEST_EXIT_CODE_PREFIX}1
        """
    )
    log_fp = tmp_path / "test.log"
    log_fp.write_text(forged_log)

    test_spec = TestSpec(
        instance_id="test-instance",
        repo="pvlib/pvlib-python",
        version="0.1",
        repo_script_list=[],
        eval_script_list=[],
        env_script_list=[],
        arch="x86_64",
        FAIL_TO_PASS=[],
        PASS_TO_PASS=[],
        language="Python",
        docker_specs={},
        namespace=None,
    )

    status_map, found = get_logs_eval(test_spec, str(log_fp))
    assert status_map == {}
    assert found is False

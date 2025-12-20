import re
from swebench.harness.constants import TestStatus
from swebench.harness.test_spec.test_spec import TestSpec


def parse_log_maven(log: str, test_spec: TestSpec) -> dict[str, str]:
    """
    Parser for test logs generated with 'mvn test'.
    Annoyingly maven will not print the tests that have succeeded. For this log
    parser to work, each test must be run individually, and then we look for
    BUILD (SUCCESS|FAILURE) in the logs.

    Args:
        log (str): log content
    Returns:
        dict: test case to test status mapping
    """
    test_status_map = {}
    current_test_name = "---NO TEST NAME FOUND YET---"

    # Get the test name from the command used to execute the test.
    # Assumes we run evaluation with set -x
    test_name_pattern = r"^.*-Dtest=(\S+).*$"
    result_pattern = r"^.*BUILD (SUCCESS|FAILURE)$"

    for line in log.split("\n"):
        test_name_match = re.match(test_name_pattern, line.strip())
        if test_name_match:
            current_test_name = test_name_match.groups()[0]

        result_match = re.match(result_pattern, line.strip())
        if result_match:
            status = result_match.groups()[0]
            if status == "SUCCESS":
                test_status_map[current_test_name] = TestStatus.PASSED.value
            elif status == "FAILURE":
                test_status_map[current_test_name] = TestStatus.FAILED.value

    return test_status_map


def parse_log_ant(log: str, test_spec: TestSpec) -> dict[str, str]:
    test_status_map = {}

    pattern = r"^\s*\[junit\]\s+\[(PASS|FAIL|ERR)\]\s+(.*)$"

    for line in log.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            status, test_name = match.groups()
            if status == "PASS":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status in ["FAIL", "ERR"]:
                test_status_map[test_name] = TestStatus.FAILED.value

    return test_status_map


def parse_log_gradle_custom(log: str, test_spec: TestSpec) -> dict[str, str]:
    """
    Parser for test logs generated with 'gradle test'. Assumes that the
    pre-install script to update the gradle config has run.

    Handles race conditions where test name and status appear on different lines
    due to interleaved log output from concurrent processes.
    """
    test_status_map = {}

    # Pattern for normal case: test name and status on the same line
    # e.g., "com.example.Test > testMethod PASSED"
    full_pattern = r"^([^>].+)\s+(PASSED|FAILED)$"

    # Pattern for test name without status (race condition case)
    # e.g., "com.example.Test > testMethod" followed by warnings, then "PASSED"
    test_name_pattern = r"^(\S+\s+>\s+\S+)$"

    # Pattern for standalone status line
    status_only_pattern = r"^(PASSED|FAILED)$"

    pending_test_name = None

    for line in log.split("\n"):
        stripped = line.strip()

        # Check for full match (test name + status on same line)
        match = re.match(full_pattern, stripped)
        if match:
            test_name, status = match.groups()
            if status == "PASSED":
                test_status_map[test_name] = TestStatus.PASSED.value
            elif status == "FAILED":
                test_status_map[test_name] = TestStatus.FAILED.value
            pending_test_name = None
            continue

        # Check for test name without status
        test_name_match = re.match(test_name_pattern, stripped)
        if test_name_match:
            pending_test_name = test_name_match.group(1)
            continue

        # Check for standalone status (applies to pending test name)
        if pending_test_name:
            status_match = re.match(status_only_pattern, stripped)
            if status_match:
                status = status_match.group(1)
                if status == "PASSED":
                    test_status_map[pending_test_name] = TestStatus.PASSED.value
                elif status == "FAILED":
                    test_status_map[pending_test_name] = TestStatus.FAILED.value
                pending_test_name = None

    return test_status_map


MAP_REPO_TO_PARSER_JAVA = {
    "google/gson": parse_log_maven,
    "apache/druid": parse_log_maven,
    "javaparser/javaparser": parse_log_maven,
    "projectlombok/lombok": parse_log_ant,
    "apache/lucene": parse_log_gradle_custom,
    "reactivex/rxjava": parse_log_gradle_custom,
}

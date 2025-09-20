"""
SWE-bench Multilingual dataset eval script generation.
This handles all repositories in the SWE-bench Multilingual datasets using common eval script generation.
"""

from swebench.data_specs import get_data_spec
from swebench.types import SWEbenchInstance
from swebench.harness.constants import (
    END_TEST_OUTPUT,
    START_TEST_OUTPUT,
)
from swebench.utils import get_modified_files, generate_heredoc_delimiter


# MARK: Test Command Creation Functions
def get_test_cmds(instance) -> list:
    test_cmd = get_data_spec(instance["repo"], instance["version"])["test_cmd"]
    return [test_cmd] if isinstance(test_cmd, str) else test_cmd


def _make_eval_script_list(
    instance, specs, env_name, repo_directory, base_commit, test_patch
) -> list:
    """
    Applies the test patch and runs the tests.
    """
    test_files = get_modified_files(test_patch)
    # Reset test files to the state they should be in before the patch.
    if test_files:
        reset_tests_command = f"git checkout {base_commit} {' '.join(test_files)}"
    else:
        reset_tests_command = 'echo "No test files to reset"'

    build_commands = []
    if "build" in specs:
        build_commands.extend(specs["build"])

    delimiter = generate_heredoc_delimiter(test_patch)
    apply_test_patch_command = (
        f"git apply --verbose --reject - <<'{delimiter}'\n{test_patch}\n{delimiter}"
    )
    test_commands = get_test_cmds(instance)
    eval_commands = [
        f"cd {repo_directory}",
        f"git config --global --add safe.directory {repo_directory}",  # for nonroot user
        f"cd {repo_directory}",
        # This is just informational, so we have a record
        # f"git status",
        # f"git show",
        # f"git -c core.fileMode=false diff {base_commit}",
        reset_tests_command,
        apply_test_patch_command,
        *build_commands,
        f": '{START_TEST_OUTPUT}'",
        *test_commands,
        f": '{END_TEST_OUTPUT}'",
        reset_tests_command,
    ]
    return eval_commands


def get_eval_script_list(instance: SWEbenchInstance) -> list[str]:
    """
    Generate eval script commands list for SWE-bench Multilingual instances.

    Args:
        instance: SWE-bench instance dictionary

    Returns:
        List of bash commands for evaluation
    """
    instance_id = instance["instance_id"]
    repo = instance["repo"]
    version = instance.get("version")
    base_commit = instance["base_commit"]
    test_patch = instance["test_patch"]

    env_name = "testbed"
    repo_directory = f"/{env_name}"
    specs = get_data_spec(repo, version)

    return _make_eval_script_list(
        instance, specs, env_name, repo_directory, base_commit, test_patch
    )


def get_eval_script(instance: SWEbenchInstance) -> str:
    """
    Generate complete eval script for SWE-bench Multilingual instances.

    Args:
        instance: SWE-bench instance dictionary

    Returns:
        Complete bash script as string
    """
    eval_script_list = get_eval_script_list(instance)

    return "\n".join(["#!/bin/bash", "set -uxo pipefail"] + eval_script_list) + "\n"

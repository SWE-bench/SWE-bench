import ast
import json
import os
import re

from typing import Any

from swebench.harness.constants import (
    END_TEST_OUTPUT,
    MAP_REPO_VERSION_TO_SPECS,
    START_TEST_OUTPUT,
)
from swebench.harness.utils import get_modified_files


# MARK: Test Command Creation Functions


DEFAULT_SPEC_VERSION_KEYS = ("default", None, "latest")


def parse_instance_list_field(
    instance: dict[str, Any], key: str, alt_keys: tuple[str, ...] = ()
) -> list[str]:
    """
    Parse a list-like instance field that may be encoded as:
    - a Python list
    - a JSON list string
    - a Python repr list string (single quotes)
    """
    value: Any = None
    for candidate_key in (key, *alt_keys):
        if candidate_key in instance:
            value = instance[candidate_key]
            break
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    if not isinstance(value, str):
        return [str(value)]

    value = value.strip()
    if not value:
        return []

    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(value)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
    else:
        inner = value
    return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]


def resolve_repo_version_spec(repo: str, version: Any) -> tuple[Any, dict]:
    """
    Resolve repo/version specs with a fallback chain for versionless datasets
    like SWE-bench Pro.
    """
    repo_specs = MAP_REPO_VERSION_TO_SPECS.get(repo)
    if repo_specs is None:
        raise KeyError(
            f"Repo '{repo}' has no harness specs in MAP_REPO_VERSION_TO_SPECS"
        )

    candidates = []
    if version is not None:
        candidates.append(version)
    candidates.extend(DEFAULT_SPEC_VERSION_KEYS)

    for candidate in candidates:
        if candidate in repo_specs:
            return candidate, repo_specs[candidate]

    if len(repo_specs) == 1:
        resolved_version = next(iter(repo_specs.keys()))
        return resolved_version, repo_specs[resolved_version]

    available = ", ".join(sorted(str(x) for x in repo_specs.keys()))
    raise KeyError(
        f"Unable to resolve specs for repo '{repo}' version '{version}'. "
        f"Available keys: {available}"
    )


def resolve_instance_spec(instance: dict[str, Any]) -> tuple[Any, dict]:
    return resolve_repo_version_spec(instance["repo"], instance.get("version"))


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _get_test_cmds_go_selected(instance: dict[str, Any], _base_test_cmd: Any) -> list[str]:
    selected = parse_instance_list_field(instance, "selected_test_files_to_run")
    test_names = []
    packages = []

    for entry in selected:
        stripped = entry.strip()
        if not stripped:
            continue
        if stripped.endswith(".go"):
            pkg_dir = os.path.dirname(stripped)
            packages.append("." if not pkg_dir else f"./{pkg_dir}")
        name_candidate = stripped.split("//", 1)[0].split("/", 1)[0].split("#", 1)[0]
        if re.match(r"^Test", name_candidate):
            test_names.append(name_candidate)

    if not packages:
        for modified in get_modified_files(instance.get("test_patch", "")):
            if modified.endswith("_test.go"):
                pkg_dir = os.path.dirname(modified)
                packages.append("." if not pkg_dir else f"./{pkg_dir}")

    packages = _dedupe_keep_order(packages)
    if not packages:
        packages = ["./..."]
    package_expr = " ".join(packages[:6])

    test_names = _dedupe_keep_order(test_names)
    if test_names:
        max_names = 32
        regex = "^(" + "|".join(re.escape(name) for name in test_names[:max_names]) + ")$"
        return [f"go test -v {package_expr} -run '{regex}'"]
    return [f"go test -v {package_expr}"]


MAP_REPO_TO_TEST_CMDS = {
    "flipt-io/flipt": _get_test_cmds_go_selected,
    "future-architect/vuls": _get_test_cmds_go_selected,
    "gravitational/teleport": _get_test_cmds_go_selected,
    "navidrome/navidrome": _get_test_cmds_go_selected,
}


def get_test_cmds(instance) -> list:
    _, specs = resolve_instance_spec(instance)
    test_cmd = specs["test_cmd"]
    if instance["repo"] in MAP_REPO_TO_TEST_CMDS:
        return MAP_REPO_TO_TEST_CMDS[instance["repo"]](instance, test_cmd)
    return [test_cmd] if isinstance(test_cmd, str) else test_cmd


# MARK: Script Creation Functions


def make_repo_script_list_common(
    specs, repo, repo_directory, base_commit, env_name
) -> list:
    """
    Create a list of bash commands to set up the repository for testing.
    This is the setup script for the instance image.
    """
    setup_commands = [
        f"git clone -o origin https://github.com/{repo} {repo_directory}",
        f"chmod -R 777 {repo_directory}",  # So nonroot user can run tests
        f"cd {repo_directory}",
        f"git reset --hard {base_commit}",
        "git remote remove origin",  # Remove the remote so the agent won't see newer commits
    ]
    if "pre_install" in specs:
        setup_commands.extend(specs["pre_install"])
    if "install" in specs:
        setup_commands.extend(specs["install"])
    if "build" in specs:
        setup_commands.extend(specs["build"])
    return setup_commands


def make_env_script_list_common(instance, specs, env_name) -> list:
    """
    Creates the list of commands to set up the environment for testing.
    This is the setup script for the environment image.
    """
    reqs_commands = []
    if "apt-pkgs" in specs:
        reqs_commands += [
            "apt-get update",
            f"apt-get install -y {' '.join(specs['apt-pkgs'])}",
        ]
    return reqs_commands


def make_eval_script_list_common(
    instance, specs, env_name, repo_directory, base_commit, test_patch
) -> list:
    """
    Applies the test patch and runs the tests.
    """
    HEREDOC_DELIMITER = "EOF_114329324912"
    test_files = get_modified_files(test_patch)
    # Reset test files to the state they should be in before the patch.
    if test_files:
        reset_tests_command = f"git checkout {base_commit} {' '.join(test_files)}"
    else:
        reset_tests_command = 'echo "No test files to reset"'

    build_commands = []
    if "build" in specs:
        build_commands.extend(specs["build"])

    apply_test_patch_command = f"git apply --verbose --reject - <<'{HEREDOC_DELIMITER}'\n{test_patch}\n{HEREDOC_DELIMITER}"
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

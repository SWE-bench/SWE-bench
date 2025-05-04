from swebench.harness.constants import MAP_REPO_TO_EXT
from swebench.harness.test_spec.javascript import (
    make_repo_script_list_js,
    make_env_script_list_js,
    make_eval_script_list_js,
)
from swebench.harness.test_spec.python import (
    make_repo_script_list_py,
    make_env_script_list_py,
    make_eval_script_list_py,
)
from swebench.harness.test_spec.utils import (
    make_env_script_list_common,
    make_eval_script_list_common,
    make_repo_script_list_common,
)


def make_repo_script_list(specs, repo, repo_directory, base_commit, env_name) -> list:
    """
    Create a list of bash commands to set up the repository for testing.
    This is the setup script for the instance image.
    """
    ext = MAP_REPO_TO_EXT[repo]
    func = {
        "c": make_repo_script_list_common,
        "go": make_repo_script_list_common,
        "java": make_repo_script_list_common,
        "js": make_repo_script_list_js,
        "php": make_repo_script_list_common,
        "py": make_repo_script_list_py,
        "rb": make_repo_script_list_common,
        "rs": make_repo_script_list_common,
    }[ext]
    return func(specs, repo, repo_directory, base_commit, env_name)


def make_env_script_list(instance, specs, env_name) -> list:
    """
    Creates the list of commands to set up the environment for testing.
    This is the setup script for the environment image.
    """
    ext = MAP_REPO_TO_EXT[instance["repo"]]
    func = {
        "c": make_env_script_list_common,
        "go": make_env_script_list_common,
        "java": make_env_script_list_common,
        "js": make_env_script_list_js,
        "php": make_env_script_list_common,
        "py": make_env_script_list_py,
        "rb": make_env_script_list_common,
        "rs": make_env_script_list_common,
    }[ext]
    return func(instance, specs, env_name)


def make_eval_script_list(
    instance, specs, env_name, repo_directory, base_commit, test_patch
) -> list:
    """
    Applies the test patch and runs the tests.
    """
    ext = MAP_REPO_TO_EXT[instance["repo"]]
    func = {
        "c": make_eval_script_list_common,
        "go": make_eval_script_list_common,
        "java": make_eval_script_list_common,
        "js": make_eval_script_list_js,
        "php": make_eval_script_list_common,
        "py": make_eval_script_list_py,
        "rb": make_eval_script_list_common,
        "rs": make_eval_script_list_common,
    }[ext]
    return func(instance, specs, env_name, repo_directory, base_commit, test_patch)

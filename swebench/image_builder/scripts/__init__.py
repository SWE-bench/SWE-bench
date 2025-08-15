from swebench.data_specs import MAP_REPO_TO_EXT
from swebench.harness.test_spec.python import (
    make_repo_script_list_py,
    make_env_script_list_py,
)
from swebench.harness.test_spec.utils import (
    make_env_script_list_common,
    make_repo_script_list_common,
)


def make_repo_script_list(specs, repo, repo_directory, base_commit, env_name) -> list:
    """
    Create a list of bash commands to set up the repository for testing.
    This is the setup script for the instance image.
    """
    ext = MAP_REPO_TO_EXT[repo]
    func = {
        "py": make_repo_script_list_py,
    }.get(ext, make_repo_script_list_common)
    return func(specs, repo, repo_directory, base_commit, env_name)


def make_env_script_list(instance, specs, env_name) -> list:
    """
    Creates the list of commands to set up the environment for testing.
    This is the setup script for the environment image.
    """
    ext = MAP_REPO_TO_EXT[instance["repo"]]
    func = {
        "py": make_env_script_list_py,
    }.get(ext, make_env_script_list_common)
    return func(instance, specs, env_name)
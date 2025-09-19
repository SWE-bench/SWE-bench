from swebench.image_builder.dockerfile_gen._swebench_multilingual.c import (
    _DOCKERFILE_BASE_C,
    MAP_REPO_VERSION_TO_SPECS_C,
)
from swebench.image_builder.dockerfile_gen._swebench_multilingual.go import (
    _DOCKERFILE_BASE_GO,
    MAP_REPO_VERSION_TO_SPECS_GO,
)
from swebench.image_builder.dockerfile_gen._swebench_multilingual.java import (
    _DOCKERFILE_BASE_JAVA,
    MAP_REPO_VERSION_TO_SPECS_JAVA,
)
from swebench.image_builder.dockerfile_gen._swebench_multilingual.javascript import (
    _DOCKERFILE_BASE_JS,
    MAP_REPO_VERSION_TO_SPECS_JS,
)
from swebench.image_builder.dockerfile_gen._swebench_multilingual.php import (
    _DOCKERFILE_BASE_PHP,
    MAP_REPO_VERSION_TO_SPECS_PHP,
)
from swebench.image_builder.dockerfile_gen._swebench_multilingual.ruby import (
    _DOCKERFILE_BASE_RUBY,
    MAP_REPO_VERSION_TO_SPECS_RUBY,
)
from swebench.image_builder.dockerfile_gen._swebench_multilingual.rust import (
    _DOCKERFILE_BASE_RUST,
    MAP_REPO_VERSION_TO_SPECS_RUST,
)

from swebench.image_builder.constants import CONTAINER_WORKDIR, CONTAINER_ENV_NAME

MAP_REPO_VERSION_TO_SPECS = {
    **MAP_REPO_VERSION_TO_SPECS_C,
    **MAP_REPO_VERSION_TO_SPECS_GO,
    **MAP_REPO_VERSION_TO_SPECS_JAVA,
    **MAP_REPO_VERSION_TO_SPECS_JS,
    **MAP_REPO_VERSION_TO_SPECS_PHP,
    **MAP_REPO_VERSION_TO_SPECS_RUBY,
    **MAP_REPO_VERSION_TO_SPECS_RUST,
}


def get_dockerfile_base(instance, docker_specs):
    if instance["repo"] in MAP_REPO_VERSION_TO_SPECS_C:
        return _DOCKERFILE_BASE_C.format(**docker_specs)
    elif instance["repo"] in MAP_REPO_VERSION_TO_SPECS_GO:
        return _DOCKERFILE_BASE_GO.format(**docker_specs)
    elif instance["repo"] in MAP_REPO_VERSION_TO_SPECS_JAVA:
        return _DOCKERFILE_BASE_JAVA.format(**docker_specs)
    elif instance["repo"] in MAP_REPO_VERSION_TO_SPECS_JS:
        return _DOCKERFILE_BASE_JS.format(**docker_specs)
    elif instance["repo"] in MAP_REPO_VERSION_TO_SPECS_PHP:
        return _DOCKERFILE_BASE_PHP.format(**docker_specs)
    elif instance["repo"] in MAP_REPO_VERSION_TO_SPECS_RUBY:
        return _DOCKERFILE_BASE_RUBY.format(**docker_specs)
    elif instance["repo"] in MAP_REPO_VERSION_TO_SPECS_RUST:
        return _DOCKERFILE_BASE_RUST.format(**docker_specs)
    else:
        raise ValueError(f"Invalid repository for multilingual: {instance['repo']}")


def make_repo_script_list(specs, repo, base_commit) -> list:
    """
    Create a list of bash commands to set up the repository for testing.
    This is the setup script for the instance image.
    """
    setup_commands = [
        *git_clone_timesafe(repo, base_commit, CONTAINER_WORKDIR),
        f"cd {CONTAINER_WORKDIR}",
    ]
    if "pre_install" in specs:
        setup_commands.extend(specs["pre_install"])
    if "install" in specs:
        setup_commands.extend(specs["install"])
    if "build" in specs:
        setup_commands.extend(specs["build"])
    return setup_commands


def make_env_script_list(specs) -> list:
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


def _get_dockerfile(instance) -> str:
    repo = instance["repo"]
    version = instance.get("version")
    base_commit = instance["base_commit"]
    specs = MAP_REPO_VERSION_TO_SPECS[repo][version]
    docker_specs = specs.get("docker_specs", {})
    env_script = make_env_script_list(specs)
    repo_script = make_repo_script_list(specs, repo, base_commit)
    monolithic_dockerfile = get_dockerfile_base(instance, docker_specs)
    monolithic_dockerfile += f"\n{env_script}\n" if env_script else ""
    monolithic_dockerfile += f'\nRUN echo "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate {CONTAINER_ENV_NAME}" > /root/.bashrc\n'
    monolithic_dockerfile += f"\n{repo_script}\n" if repo_script else ""
    monolithic_dockerfile += f"\nWORKDIR {CONTAINER_WORKDIR}\n"
    return monolithic_dockerfile

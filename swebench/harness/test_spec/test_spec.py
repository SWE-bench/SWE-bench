import hashlib
import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union, cast

from swebench.harness.constants import (
    DEFAULT_DOCKER_SPECS,
    KEY_INSTANCE_ID,
    LATEST,
    MAP_REPO_TO_EXT,
    MAP_REPO_VERSION_TO_SPECS,
    SWEbenchInstance,
)
from swebench.harness.dockerfiles import (
    _DOCKERFILE_ENV,
    _DOCKERFILE_ENV_AGNOSTIC,
    get_dockerfile_base,
    get_dockerfile_env,
    get_dockerfile_instance,
)
from swebench.harness.test_spec.create_scripts import (
    make_repo_script_list,
    make_env_script_list,
    make_eval_script_list,
)


def load_dockerfile_content(dockerfile_spec, base_dir: str | Path | None = None) -> str | None:
    """
    Load Dockerfile content from a specification dict.
    
    The dockerfile_spec should be a dict with exactly one of:
    - {"path": "path/to/dockerfile"} - load from file
    - {"contents": "FROM ubuntu:22.04..."} - use directly
    
    Args:
        dockerfile_spec: Dict with 'path' or 'contents', or None
        base_dir: Base directory for resolving relative paths (e.g., task_dir)
        
    Returns:
        Dockerfile content as string, or None if dockerfile_spec is None
        
    Raises:
        ValueError: If dockerfile_spec format is invalid
        FileNotFoundError: If path is specified but file doesn't exist
    """
    if dockerfile_spec is None:
        return None
    
    if not isinstance(dockerfile_spec, dict):
        raise ValueError(
            f"dockerfile_spec must be a dict with 'path' or 'contents', got {type(dockerfile_spec).__name__}"
        )
    
    has_path = "path" in dockerfile_spec
    has_contents = "contents" in dockerfile_spec
    
    if has_path and has_contents:
        raise ValueError(
            "dockerfile_spec cannot specify both 'path' and 'contents'. "
            "Use either {'path': '...'} or {'contents': '...'}"
        )
    
    if not has_path and not has_contents:
        raise ValueError(
            "dockerfile_spec must specify either 'path' or 'contents'. "
            "Got: " + str(dockerfile_spec)
        )
    
    if has_path:
        path = Path(dockerfile_spec["path"])
        # Resolve relative paths against base_dir if provided
        if base_dir is not None and not path.is_absolute():
            path = Path(base_dir) / path
        if not path.exists():
            raise FileNotFoundError(
                f"Dockerfile not found at path: {path}\n"
                f"Specified in dockerfile_spec: {dockerfile_spec}"
            )
        if not path.is_file():
            raise ValueError(
                f"Dockerfile path is not a file: {path}\n"
                f"Specified in dockerfile_spec: {dockerfile_spec}"
            )
        return path.read_text()
    
    if has_contents:
        contents = dockerfile_spec["contents"]
        if not isinstance(contents, str):
            raise ValueError(
                f"dockerfile_spec 'contents' must be a string, got {type(contents).__name__}"
            )
        return contents
    
    # Should never reach here due to earlier checks
    raise ValueError(f"Invalid dockerfile_spec: {dockerfile_spec}")


@dataclass
class TestSpec:
    """
    A dataclass that represents a test specification for a single instance of SWE-bench.
    """

    instance_id: str
    repo: str
    version: str
    repo_script_list: list[str]
    eval_script_list: list[str]
    env_script_list: list[str]
    arch: str
    FAIL_TO_PASS: list[str]
    PASS_TO_PASS: list[str]
    language: str
    docker_specs: dict
    namespace: Optional[str]
    base_image_tag: str = LATEST
    env_image_tag: str = LATEST
    instance_image_tag: str = LATEST
    custom_dockerfile_base: Optional[str] = None
    custom_dockerfile_env: Optional[str] = None
    custom_dockerfile_instance: Optional[str] = None

    @property
    def setup_env_script(self):
        return (
            "\n".join(["#!/bin/bash", "set -euxo pipefail"] + self.env_script_list)
            + "\n"
        )

    @property
    def eval_script(self):
        return (
            "\n".join(["#!/bin/bash", "set -uxo pipefail"] + self.eval_script_list)
            + "\n"
        )
        # Don't exit early because we need to revert tests at the end

    @property
    def install_repo_script(self):
        return (
            "\n".join(["#!/bin/bash", "set -euxo pipefail"] + self.repo_script_list)
            + "\n"
        )

    @property
    def base_image_key(self):
        """
        If docker_specs or custom_dockerfile_base are present, the base image key includes a hash of the specs.
        
        Otherwise, the base image key is just the language and arch.
        """
        if self.docker_specs != {} or self.custom_dockerfile_base is not None:
            # Hash the formatted Dockerfile content, not the template
            # This ensures the hash represents the actual Dockerfile that will be built
            hash_key = self.base_dockerfile
            hash_object = hashlib.sha256()
            hash_object.update(hash_key.encode("utf-8"))
            hash_value = hash_object.hexdigest()
            val = hash_value[
                :10
            ]  # 10 characters is still likely to be unique given only a few base images will be created
            return f"sweb.base.{self.language}.{self.arch}.{val}:{self.base_image_tag}"
        return (
            f"sweb.base.{self.language}.{self.arch}:{self.base_image_tag}"
        )

    @property
    def env_image_key(self):
        """
        The key for the environment image is based on the hash of the environment script list and Dockerfile.
        If either changes, the image will be rebuilt automatically.

        Note that old images are not automatically deleted, so consider cleaning up old images periodically.
        """
        # Hash both the setup scripts and the formatted Dockerfile
        # The env_dockerfile already incorporates docker_specs in its formatting
        hash_key = str(self.env_script_list)
        hash_key += self.env_dockerfile
        hash_object = hashlib.sha256()
        hash_object.update(hash_key.encode("utf-8"))
        hash_value = hash_object.hexdigest()
        val = hash_value[:22]  # 22 characters is still very likely to be unique
        return f"sweb.env.{self.language}.{self.arch}.{val}:{self.env_image_tag}"

    @property
    def instance_image_key(self):
        key = f"sweb.eval.{self.arch}.{self.instance_id.lower()}:{self.instance_image_tag}"
        if self.is_remote_image:
            key = f"{self.namespace}/{key}".replace("__", "_1776_")
        return key

    @property
    def is_remote_image(self):
        return self.namespace is not None

    def get_instance_container_name(self, run_id=None):
        if not run_id:
            return f"sweb.eval.{self.instance_id}"
        return f"sweb.eval.{self.instance_id.lower()}.{run_id}"

    @property
    def base_dockerfile(self):
        if self.custom_dockerfile_base is not None:
            # Format custom dockerfile with same variables as default
            if self.arch == "arm64":
                conda_arch = "aarch64"
            else:
                conda_arch = self.arch
            return self.custom_dockerfile_base.format(
                platform=self.platform,
                conda_arch=conda_arch,
                **{**DEFAULT_DOCKER_SPECS, **self.docker_specs},
            )
        return get_dockerfile_base(
            self.platform,
            self.arch,
            self.language,
            **{**DEFAULT_DOCKER_SPECS, **self.docker_specs},
        )

    @property
    def env_dockerfile(self):
        if self.custom_dockerfile_env is not None:
            # Format custom dockerfile with same variables as default
            return self.custom_dockerfile_env.format(
                platform=self.platform,
                arch=self.arch,
                base_image_key=self.base_image_key,
                **{**DEFAULT_DOCKER_SPECS, **self.docker_specs},
            )
        
        # For languages without separate env Dockerfiles (Go, C, Java, PHP, Ruby, Rust),
        # if custom_dockerfile_base is set, just use the base image directly
        # instead of rebuilding it with the default base Dockerfile.
        # Check if language has a dedicated env Dockerfile in _DOCKERFILE_ENV
        if self.custom_dockerfile_base is not None and self.language not in _DOCKERFILE_ENV:
            # Return the agnostic env Dockerfile that just references the custom base image
            # This avoids rebuilding the custom base image unnecessarily
            return _DOCKERFILE_ENV_AGNOSTIC.format(
                platform=self.platform,
                base_image_key=self.base_image_key,
            )
        
        return get_dockerfile_env(
            self.platform,
            self.arch,
            self.language,
            self.base_image_key,
            **{**DEFAULT_DOCKER_SPECS, **self.docker_specs},
        )

    @property
    def instance_dockerfile(self):
        if self.custom_dockerfile_instance is not None:
            # Format custom dockerfile with same variables as default
            return self.custom_dockerfile_instance.format(
                platform=self.platform,
                env_image_name=self.env_image_key,
            )
        return get_dockerfile_instance(self.platform, self.language, self.env_image_key)

    @property
    def platform(self):
        if self.arch == "x86_64":
            return "linux/x86_64"
        elif self.arch == "arm64":
            return "linux/arm64/v8"
        else:
            raise ValueError(f"Invalid architecture: {self.arch}")


def get_test_specs_from_dataset(
    dataset: Union[list[SWEbenchInstance], list[TestSpec]],
    namespace: Optional[str] = None,
    instance_image_tag: str = LATEST,
    env_image_tag: str = LATEST,
    cli_docker_specs: Optional[dict] = None,
) -> list[TestSpec]:
    """
    Idempotent function that converts a list of SWEbenchInstance objects to a list of TestSpec objects.
    """
    if isinstance(dataset[0], TestSpec):
        return cast(list[TestSpec], dataset)
    return list(
        map(
            lambda x: make_test_spec(x, namespace, instance_image_tag, env_image_tag, cli_docker_specs=cli_docker_specs),
            cast(list[SWEbenchInstance], dataset),
        )
    )


def make_test_spec(
    instance: SWEbenchInstance,
    namespace: Optional[str] = None,
    base_image_tag: str = LATEST,
    env_image_tag: str = LATEST,
    instance_image_tag: str = LATEST,
    arch: str = "x86_64",
    cli_docker_specs: Optional[dict] = None,
) -> TestSpec:
    if isinstance(instance, TestSpec):
        return instance
    assert base_image_tag is not None, "base_image_tag cannot be None"
    assert env_image_tag is not None, "env_image_tag cannot be None"
    assert instance_image_tag is not None, "instance_image_tag cannot be None"
    instance_id = instance[KEY_INSTANCE_ID]
    repo = instance["repo"]
    version = instance.get("version")
    base_commit = instance["base_commit"]
    problem_statement = instance.get("problem_statement")
    hints_text = instance.get("hints_text")  # Unused
    test_patch = instance["test_patch"]

    def _from_json_or_obj(key: str) -> Any:
        """If key points to string, load with json"""
        if key not in instance:
            # If P2P, F2P keys not found, it's a validation instance
            return []
        if isinstance(instance[key], str):
            return json.loads(instance[key])
        return instance[key]

    pass_to_pass = _from_json_or_obj("PASS_TO_PASS")
    fail_to_pass = _from_json_or_obj("FAIL_TO_PASS")

    env_name = "testbed"
    repo_directory = f"/{env_name}"
    # Safe lookup for specs - returns empty dict if repo/version not in hardcoded map
    specs = MAP_REPO_VERSION_TO_SPECS.get(repo, {}).get(version, {})
    docker_specs = specs.get("docker_specs", {})
    
    # Merge CLI docker specs (CLI overrides config)
    if cli_docker_specs:
        docker_specs = {**docker_specs, **cli_docker_specs}

    repo_script_list = make_repo_script_list(
        specs, repo, repo_directory, base_commit, env_name
    )
    env_script_list = make_env_script_list(instance, specs, env_name)
    eval_script_list = make_eval_script_list(
        instance, specs, env_name, repo_directory, base_commit, test_patch
    )
    
    # Extract and load custom dockerfile content if specified
    # Resolve paths relative to task_dir if present
    task_dir = instance.get("task_dir")
    custom_dockerfile_base = load_dockerfile_content(instance.get("dockerfile_base"), task_dir)
    custom_dockerfile_env = load_dockerfile_content(instance.get("dockerfile_env"), task_dir)
    custom_dockerfile_instance = load_dockerfile_content(instance.get("dockerfile_instance"), task_dir)
    
    return TestSpec(
        instance_id=instance_id,
        repo=repo,
        env_script_list=env_script_list,
        repo_script_list=repo_script_list,
        eval_script_list=eval_script_list,
        version=version,
        arch=arch,
        FAIL_TO_PASS=fail_to_pass,
        PASS_TO_PASS=pass_to_pass,
        language=MAP_REPO_TO_EXT.get(repo, "custom"),
        docker_specs=docker_specs,
        namespace=namespace,
        base_image_tag=base_image_tag,
        env_image_tag=env_image_tag,
        instance_image_tag=instance_image_tag,
        custom_dockerfile_base=custom_dockerfile_base,
        custom_dockerfile_env=custom_dockerfile_env,
        custom_dockerfile_instance=custom_dockerfile_instance,
    )

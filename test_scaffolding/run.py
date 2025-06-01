from swebench.harness.constants import SWEbenchInstance
from swebench.harness.test_spec.test_spec import TestSpec, make_test_spec
from swebench.harness.docker_build import (
    build_env_images,
    build_container,
)
from swebench.harness.docker_utils import copy_to_container

from datasets import load_dataset
import docker

import argparse
import logging
import time
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_task_instance_by_id(dataset, instance_id, split="test"):
    """
    Find a task instance in a SWE-bench family dataset by its instance ID.
    """
    dataset = dataset[split]
    for task in dataset:
        if task["instance_id"] == instance_id:
            return task
    return None


def build_task_instance_container(test_spec, run_id, client):
    # First build the base environment image
    build_env_images(client, [test_spec])
    # Then build the instance image and create the container
    container = build_container(
        test_spec,
        client,
        run_id=run_id,
        nocache=False,
        logger=logging.getLogger(__name__),
    )

    return container


def run_tests(container, test_command, log_dir, before_patch=True):
    bash_cmd = (
        f'/bin/bash -lc "{test_command}"'  # Use -lc to run the command in a login shell
    )
    logger.info(f"Running inside container: {bash_cmd!r}")
    exec_result = container.exec_run(
        bash_cmd,
        workdir="/testbed",
        stdout=True,
        stderr=True,
    )

    base_filename = "before_patch.log" if before_patch else "after_patch.log"
    output_filename = os.path.join(log_dir, base_filename)
    with open(output_filename, "wb") as outfile:
        outfile.write(exec_result.output)

    if exec_result.exit_code == 0:
        logger.info(f"Tests completed successfully. Output → {output_filename!r}")
    else:
        logger.warning(
            f"Tests failed (exit code {exec_result.exit_code}). "
            f"See {output_filename!r} for details."
        )


def apply_patch(container, patch_content, log_dir, is_test_patch=False):
    patch_filename = "test_patch.diff" if is_test_patch else "patch.diff"
    with open(f"{log_dir}/{patch_filename}", "w") as patch_file:
        patch_file.write(patch_content)
    copy_to_container(
        container,
        Path(f"{log_dir}/{patch_filename}"),
        Path(f"/testbed/{patch_filename}"),
    )
    logger.info("Patch file copied to container.")

    git_apply_command = f"git apply /testbed/{patch_filename}"
    logger.info(f"Applying patch with command: {git_apply_command!r}")

    exec_result = container.exec_run(
        git_apply_command,
        workdir="/testbed",
        stdout=True,
        stderr=True,
    )
    if exec_result.exit_code == 0:
        logger.info(f"Patch {patch_filename} applied successfully.")
    else:
        logger.warning(f"Patch {patch_filename} failed (exit code {exec_result.exit_code}).")


def main():
    client = docker.from_env()
    dataset = load_dataset("princeton-nlp/SWE-bench_Verified")

    parser = argparse.ArgumentParser(
        description="Run the full test suite on SWE-bench Verified task instances."
    )
    parser.add_argument(
        "--instance-id",
        type=str,
        required=True,
        help="The instance ID of the SWE-bench task to run tests on.",
    )
    # Reason we need to pass in the test command is it can be different for each instance,
    # e.g. pytest (astropy-12907) vs ./tests/runtests.py (django-11066)
    # Might be able to fix this by studying how the test command is built in `run_evaluation.py`
    parser.add_argument(
        "--test-command", type=str, required=True, help="The command to run the tests."
    )
    parser.add_argument(
        "--patch-file",
        type=str,
        help="Alternative patch file location for the SWE-bench task. If not provided, the gold patch from the dataset will be used.",
    )
    parser.add_argument(
        "--remove-container",
        action="store_true",
        help="Whether to remove the container after running tests.",
    )

    # Set up args
    args = parser.parse_args()
    instance_id = args.instance_id
    test_command = args.test_command

    run_id = f"run-{instance_id}-{int(time.time())}"
    log_dir = f"./{run_id}/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Make SWE-bench TestSpec from the instance ID
    task = find_task_instance_by_id(dataset, instance_id)
    swebench_instance = SWEbenchInstance(task)
    test_spec: TestSpec = make_test_spec(swebench_instance)

    if args.patch_file:
        # If a patch file is provided, read it
        logger.info(f"Using patch file: {args.patch_file}")
        with open(args.patch_file, "r") as f:
            patch_content = f.read()
    else:
        patch_content = swebench_instance.get("patch", "")
    test_patch_content = swebench_instance.get("test_patch", "")

    if test_spec.arch != "arm64":
        logger.warning(
            f"Warning: Instance {instance_id} is using arch {test_spec.arch}. The container build will not work on ARM machines."
        )

    container = build_task_instance_container(test_spec, run_id, client)
    container.start()
    logger.info(f"Container {container.name} started for instance {instance_id}.")

    # Apply test_patch
    if test_patch_content:
        logger.info(f"Applying test patch for instance {instance_id}.")
        apply_patch(container, test_patch_content, log_dir, is_test_patch=True)

    # Run the tests before patching
    run_tests(container, test_command, log_dir, before_patch=True)

    # Apply the patch
    if patch_content:
        logger.info(f"Applying patch for instance {instance_id}.")
        apply_patch(container, patch_content, log_dir, is_test_patch=False)

    # Run the tests after patching
    run_tests(container, test_command, log_dir, before_patch=False)

    # Cleanup
    logger.info(f"Stopping container {container.name}.")
    container.stop()
    logger.info(f"Container {container.name} stopped.")
    if args.remove_container:
        container.remove()
        logger.info(f"Container {container.name} removed.")


if __name__ == "__main__":
    main()

# This file contains logic for running evaluations on Beam: <https://github.com/beam-cloud/beta9>.

from __future__ import annotations

import asyncio
import json
from beam import Image, function, Sandbox
import tenacity
import time
import traceback

from dataclasses import dataclass
from pathlib import Path
from swebench.harness.docker_build import setup_logger
from swebench.harness.reporting import make_run_report
from swebench.harness.utils import EvaluationError
from typing import cast

SANDBOX_ENTRYPOINT = "run_evaluation_beam_entrypoint"
LOCAL_SANDBOX_ENTRYPOINT_PATH = (
    Path(__file__).parent / f"{SANDBOX_ENTRYPOINT}.py"
).resolve()
REMOTE_SANDBOX_ENTRYPOINT_PATH = f"/workspace/{SANDBOX_ENTRYPOINT}.py"

swebench_image = Image().add_python_packages(["swebench", "tenacity"])

SANDBOX_TIMEOUT = 60 * 30

from swebench.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
    RUN_EVALUATION_LOG_DIR,
)
from swebench.harness.grading import get_eval_report
from swebench.harness.test_spec.test_spec import make_test_spec, TestSpec


@dataclass
class TestOutput:
    instance_id: str
    test_output: str
    report_json_str: str
    run_instance_log: str
    patch_diff: str
    log_dir: Path
    errored: bool


class BeamSandboxRuntime:
    """
    Runtime for running instances in a Beam Sandbox.
    """

    def __init__(
        self, test_spec: TestSpec, timeout: int | None = None, verbose: bool = True
    ):
        self.test_spec = test_spec
        self.verbose = verbose

        self.image = BeamSandboxRuntime.get_instance_image(test_spec)
        self.sandbox = self._get_sandbox(timeout)

        # Upload and execute setup scripts
        import tempfile
        import os

        # Upload env setup script
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
            f.write(test_spec.setup_env_script)
            env_script_path = f.name
        self.sandbox.fs.upload_file(env_script_path, "/workspace/setup_env.sh")
        os.unlink(env_script_path)

        # Upload repo setup script
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
            f.write(test_spec.install_repo_script)
            repo_script_path = f.name
        self.sandbox.fs.upload_file(repo_script_path, "/workspace/setup_repo.sh")
        os.unlink(repo_script_path)

        # Make scripts executable and run them
        self.exec("chmod +x /workspace/setup_env.sh")
        self.exec("chmod +x /workspace/setup_repo.sh")

        # Run env setup script
        output, returncode = self.exec("/bin/bash -c 'source ~/.bashrc && /workspace/setup_env.sh'")
        if returncode != 0:
            print(f"[Beam] Warning: env setup script failed with code {returncode}")
            if self.verbose:
                print(output)

        # Configure conda activation
        self.exec("echo 'source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed' >> /workspace/.bashrc")

        # Run repo setup script
        output, returncode = self.exec("/bin/bash /workspace/setup_repo.sh")
        if returncode != 0:
            print(f"[Beam] Warning: repo setup script failed with code {returncode}")
            if self.verbose:
                print(output)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    def _get_sandbox(self, timeout: int | None = None):
        # Sometimes network flakiness causes the image build to fail,
        # so we retry a few times.
        if timeout is None:
            # Default 30 minutes
            timeout = SANDBOX_TIMEOUT

        sb = Sandbox(image=self.image, keep_warm_seconds=timeout, cpu=1)

        sandbox = sb.create()

        sandbox.fs.upload_file(
            str(LOCAL_SANDBOX_ENTRYPOINT_PATH),
            REMOTE_SANDBOX_ENTRYPOINT_PATH
        )

        return sandbox

    def write_file(self, file_path: str, content: str):
        """Write content to a file in the sandbox using Beam's file system API."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as f:
            f.write(content)
            temp_path = f.name
        try:
            self.sandbox.fs.upload_file(temp_path, file_path)
        finally:
            os.unlink(temp_path)

    def exec(self, command: str) -> tuple[str, int]:
        """
        Execute a command in the sandbox using Beam's process manager.

        Returns:
            tuple[str, int]: Sandbox output and return code.
        """
        # Execute command via Beam's process manager
        if self.verbose:
            print(f"[Beam] Executing command: {command[:100]}...")
        p = self.sandbox.process.exec("python3", "-m", SANDBOX_ENTRYPOINT, command) # TODO: Use python3 instead of the full path

        # Wait for process to complete
        if self.verbose:
            print(f"[Beam] Waiting for command to complete...")
        exit_code = p.wait()

        # Read all output at once using the logs stream
        output = p.logs.read()

        if self.verbose:
            print(f"[Beam] Command completed with exit code: {exit_code}")
            if output:
                print(output)

        return output, exit_code

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up sandbox resources."""
        try:
            self.sandbox.terminate()
        except Exception:
            pass

    @staticmethod
    def get_instance_image(test_spec: TestSpec) -> Image:
        # Build shared base image with dependencies (no instance-specific scripts)
        # Scripts will be uploaded to sandbox after creation
        return (
            Image.from_registry("ubuntu:22.04").add_python_version("python3.11")
            .add_commands([
                # Install system packages
                "apt-get update && apt-get install -y wget git build-essential libffi-dev libtiff-dev jq curl locales locales-all tzdata",
                # Install miniconda
                "wget 'https://repo.anaconda.com/miniconda/Miniconda3-py311_23.11.0-2-Linux-x86_64.sh' -O /tmp/miniconda.sh",
                "bash /tmp/miniconda.sh -b -p /opt/miniconda3",
                "echo 'export PATH=/opt/miniconda3/bin:$PATH' >> ~/.bashrc",
                "/opt/miniconda3/bin/conda init --all",
                "/opt/miniconda3/bin/conda config --append channels conda-forge",
                # Add user
                "adduser --disabled-password --gecos 'dog' nonroot",
            ])
        )


def get_log_dir(pred: dict, run_id: str, instance_id: str) -> Path:
    model_name_or_path = cast(
        str, pred.get("model_name_or_path", "None").replace("/", "__")
    )
    return RUN_EVALUATION_LOG_DIR / run_id / model_name_or_path / instance_id


@function(
    image=swebench_image,
    timeout=120 * 60,  # Much larger than default timeout to account for image build time
)
def run_instance_beam(
    test_spec: TestSpec,
    pred: dict,
    run_id: str,
    timeout: int | None = None,
) -> TestOutput:
    """
    Run a single instance with the given prediction.

    Args:
        test_spec (TestSpec): TestSpec instance
        pred (dict): Prediction w/ model_name_or_path, model_patch, instance_id
        run_id (str): Run ID
        timeout (int): Timeout for running tests
    """
    instance_id = test_spec.instance_id
    print(f"\n{'='*80}")
    print(f"[Beam] Starting evaluation for {instance_id}")
    print(f"{'='*80}\n")

    log_dir = get_log_dir(pred, run_id, instance_id)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "run_instance.log"

    logger = setup_logger(instance_id, log_file, add_stdout=True)

    try:
        runner = BeamSandboxRuntime(test_spec, timeout)
    except Exception as e:
        print(f"Error creating sandbox: {e}")
        raise EvaluationError(
            instance_id,
            f"Error creating sandbox: {e}",
            logger,
        ) from e

    patch_diff = pred.get("model_patch", "")

    try:
        patch_file = "/tmp/patch.diff"
        runner.write_file(patch_file, patch_diff)

        apply_patch_output, returncode = runner.exec(
            "cd /testbed && git apply -v /tmp/patch.diff",
        )

        if returncode != 0:
            logger.info("Failed to apply patch to container, trying again...")

            apply_patch_output, returncode = runner.exec(
                "cd /testbed && patch --batch --fuzz=5 -p1 -i /tmp/patch.diff",
            )

            if returncode != 0:
                logger.info(f"{APPLY_PATCH_FAIL}:\n{apply_patch_output}")
                raise EvaluationError(
                    instance_id,
                    f"{APPLY_PATCH_FAIL}:\n{apply_patch_output}",
                    logger,
                )
            else:
                logger.info(f"{APPLY_PATCH_PASS}:\n{apply_patch_output}")
        else:
            logger.info(f"{APPLY_PATCH_PASS}:\n{apply_patch_output}")

        # Get git diff before running eval script
        git_diff_output_before, returncode = runner.exec(
            "cd /testbed && git diff",
        )
        logger.info(f"Git diff before:\n{git_diff_output_before}")

        eval_file = "/workspace/eval.sh"
        eval_script = test_spec.eval_script
        # django hack
        eval_script = eval_script.replace("locale-gen", "locale-gen en_US.UTF-8")
        runner.write_file(eval_file, eval_script)

        start_time = time.time()

        run_command = "cd /testbed"
        # pylint hack
        if "pylint" in test_spec.instance_id:
            run_command += " && PYTHONPATH="
        # increase recursion limit for testing
        run_command += " && python3 -c 'import sys; sys.setrecursionlimit(10000)'"
        # run eval script
        run_command += " && /bin/bash /workspace/eval.sh"
        test_output, returncode = runner.exec(run_command)

        total_runtime = time.time() - start_time

        test_output_path = log_dir / "test_output.txt"
        logger.info(f"Test runtime: {total_runtime:_.2f} seconds")
        with open(test_output_path, "w") as f:
            f.write(test_output)
            logger.info(f"Test output for {instance_id} written to {test_output_path}")
            print(f"Test output for {instance_id} written to {test_output_path}")

        # Get git diff after running eval script
        git_diff_output_after, returncode = runner.exec("cd /testbed && git diff")

        # Check if git diff changed after running eval script
        logger.info(f"Git diff after:\n{git_diff_output_after}")
        if git_diff_output_after != git_diff_output_before:
            logger.info("Git diff changed after running eval script")

        # Get report from test output
        logger.info(f"Grading answer for {instance_id}...")
        report = get_eval_report(
            test_spec=test_spec,
            prediction=pred,
            test_log_path=test_output_path,
            include_tests_status=True,
        )
        logger.info(
            f"report: {report}\n"
            f"Result for {instance_id}: resolved: {report[instance_id]['resolved']}"
        )


        return TestOutput(
            instance_id=instance_id,
            test_output=test_output,
            report_json_str=json.dumps(report, indent=4),
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=False,
        )
    except EvaluationError:
        error_msg = traceback.format_exc()
        logger.info(error_msg)
        print(f"[Beam] ✗ Evaluation error for {instance_id}")
        print(f"{'='*80}\n")
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )
    except Exception as e:
        error_msg = (
            f"Error in evaluating model for {instance_id}: {e}\n"
            f"{traceback.format_exc()}\n"
            f"Check ({logger.log_file}) for more information."
        )
        logger.error(error_msg)
        print(f"[Beam] ✗ Exception occurred for {instance_id}: {e}")
        print(f"{'='*80}\n")
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )


def run_instances_beam(
    predictions: dict,
    instances: list,
    full_dataset: list,
    run_id: str,
    timeout: int,
):
    """
    Run all instances for the given predictions on Beam.

    Args:
        predictions (dict): Predictions dict generated by the model
        instances (list): List of instances
        run_id (str): Run ID
        timeout (int): Timeout for running tests
    """
    print(f"\n[Beam] Starting Beam evaluation run: {run_id}")
    print(f"[Beam] Total instances in dataset: {len(instances)}")

    test_specs = list(map(make_test_spec, instances))

    run_test_specs = []

    # Check for instances that have already been run
    for test_spec in test_specs:
        log_dir = get_log_dir(
            predictions[test_spec.instance_id], run_id, test_spec.instance_id
        )
        if log_dir.exists():
            continue
        run_test_specs.append(test_spec)

    if run_test_specs:
        # Prepare argument tuples for mapping
        args_list = [
            (
                test_spec,
                predictions[test_spec.instance_id],
                run_id,
                timeout,
            )
            for test_spec in run_test_specs
        ]

        # Run instances that haven't been run yet
        # Beam's .map() takes an iterable and passes each element to the function
        results = list(run_instance_beam.map(args_list))

        for result in results:
            if result is None or isinstance(result, Exception):
                print(f"Result failed with error: {result}")
                continue

            if not isinstance(result, TestOutput):
                print(f"Unexpected result type: {type(result)}")
                continue

            # Save logs locally
            log_dir = result.log_dir
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "run_instance.log", "w") as f:
                f.write(result.run_instance_log)
            with open(log_dir / "test_output.txt", "w") as f:
                f.write(result.test_output)
            with open(log_dir / "patch.diff", "w") as f:
                f.write(result.patch_diff)
            with open(log_dir / "report.json", "w") as f:
                try:
                    report_json = json.loads(result.report_json_str)
                    json.dump(report_json, f, indent=4)
                except json.JSONDecodeError:
                    print(f"{result.instance_id}: no report.json")

    make_run_report(predictions, full_dataset, run_id)

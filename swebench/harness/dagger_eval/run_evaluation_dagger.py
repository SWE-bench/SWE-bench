# This file contains logic for running evaluations with Dagger: <https://dagger.io/>.

import functools
import json
import logging
import time
from dataclasses import dataclass, field
from logging import Logger
import io

import anyio
import dagger
from anyio import to_thread
from dagger import dag, telemetry
from opentelemetry import trace


from swebench.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
    RUN_EVALUATION_LOG_DIR,
)
from swebench.harness.constants import KEY_INSTANCE_ID, SWEbenchInstance
from swebench.harness.grading import get_eval_report
from swebench.harness.reporting import make_run_report
from swebench.harness.test_spec.test_spec import TestSpec, make_test_spec

RUN_LOG_FILE = "run_instance.log"
TEST_LOG_FILE = "test_output.txt"
PATCH_FILE = "patch.diff"
REPORT_FILE = "report.json"


tracer = telemetry.get_tracer()

logging.getLogger("httpx").setLevel(logging.ERROR)


@dataclass
class Instance:
    run_id: str
    test_spec: TestSpec
    pred: dict
    log: io.StringIO = field(default_factory=io.StringIO)

    @property
    def id(self) -> str:
        return self.test_spec.instance_id

    @property
    def log_dir(self) -> anyio.Path:
        return (
            anyio.Path(RUN_EVALUATION_LOG_DIR)
            / self.run_id
            / self.pred.get("model_name_or_path", "None").replace("/", "__")
            / self.id
        )

    async def write_file(self, filename: str, content: str):
        await (self.log_dir / filename).write_text(content)

    def setup_logger(self) -> Logger:
        # TODO: Loggers are never freed. We can optimize memory by using a single
        # logger for all instances, with a logger adapter and filter.
        logger = logging.getLogger(self.id)
        # Buffering in memory until the end of the instance run to write
        # the whole log to a file in one go avoids an issue with too many
        # open files. It's also non-blocking.
        handler = logging.StreamHandler(self.log)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger


@tracer.start_as_current_span("setup base container")
async def _build_base_image(test_spec: TestSpec) -> dagger.Container:
    if test_spec.is_remote_image:
        return dag.container().from_(test_spec.instance_image_key)

    conda_arch = test_spec.arch
    if conda_arch == "arm64":
        conda_arch = "aarch64"
    return await (
        dag.container()
        .from_("ubuntu:22.04")
        .with_exec(["apt", "update"])
        .with_env_variable("DEBIAN_FRONTEND", "noninteractive")
        .with_env_variable("TZ", "Etc/UTC")
        .with_exec(
            [
                "apt",
                "install",
                "-y",
                "wget",
                "git",
                "build-essential",
                "libffi-dev",
                "libtiff-dev",
                "python3",
                "python3-pip",
                "python-is-python3",
                "jq",
                "curl",
                "locales",
                "locales-all",
                "tzdata",
            ]
        )
        .with_file(
            "miniconda.sh",
            dag.http(
                f"https://repo.anaconda.com/miniconda/Miniconda3-py311_23.11.0-2-Linux-{conda_arch}.sh"
            ),
        )
        .with_exec(["bash", "miniconda.sh", "-b", "-p", "/opt/miniconda3"])
        .with_env_variable("PATH", "/opt/miniconda3/bin:$PATH", expand=True)
        .with_exec(["conda", "init", "--all"])
        .with_exec(["conda", "config", "--append", "channels", "conda-forge"])
        .with_exec(["adduser", "--disabled-password", "--gecos", "'dog'", "nonroot"])
        .with_new_file(
            "/root/setup_env.sh",
            test_spec.setup_env_script,
            permissions=0o500,
        )
        .with_exec(["bash", "-c", "source ~/.bashrc && /root/setup_env.sh"])
        .with_exec(
            [
                "bash",
                "-c",
                "echo 'source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed' > /root/.bashrc",
            ]
        )
        .with_new_file("/root/setup_repo.sh", test_spec.install_repo_script)
        .with_exec(["bash", "/root/setup_repo.sh"])
        .with_workdir("/testbed")
        .sync()
    )


@tracer.start_as_current_span("apply patch")
async def _run_instance_patch(
    instance: Instance, ctr: dagger.Container, logger: Logger
) -> dagger.Container:
    patch_diff = instance.pred.get("model_patch", "")
    await instance.write_file(PATCH_FILE, patch_diff)

    patch_file = f"/tmp/{PATCH_FILE}"
    ctr = ctr.with_new_file(patch_file, patch_diff)
    patched_ctr = ctr.with_exec(["git", "apply", "-v", patch_file])
    logger.info("Applying intermediate patch to container...")

    try:
        apply_patch_output = await patched_ctr.stdout()
    except dagger.ExecError:
        logger.info("Failed to apply patch to container, trying again...")
        patched_ctr = ctr.with_exec(
            [
                "patch",
                "--batch",
                "--fuzz=5",
                "-p1",
                "-i",
                patch_file,
            ],
        )
        try:
            apply_patch_output = await patched_ctr.stdout()
        except dagger.ExecError as e:
            logger.exception(f"{APPLY_PATCH_FAIL}:\n%s%s", e.stdout, e.stderr)
            raise

    logger.info(f"{APPLY_PATCH_PASS}:\n%s", apply_patch_output)

    return patched_ctr


@tracer.start_as_current_span("run evaluation script")
async def _run_evaluation_script(
    instance: Instance,
    ctr: dagger.Container,
    logger: Logger,
    timeout: int | None = None,
) -> dagger.Container:
    # Get git diff before running eval script
    git_diff_output_before = await ctr.with_exec(["git", "diff"]).stdout()

    logger.info("Git diff before:\n%s", git_diff_output_before)

    start_time = time.time()
    test_output = ""
    with anyio.move_on_after(timeout) as scope:
        for command in instance.test_spec.eval_script_list:
            if command in (
                "source /opt/miniconda3/bin/activate",
                "conda activate testbed",
            ):
                continue

            # django hack
            command = command.replace("locale-gen", "locale-gen en_US.UTF-8")

            with tracer.start_as_current_span(command) as span:
                ctr = ctr.with_exec(
                    ["conda", "run", "-n", "testbed", "bash", "-c", command],
                    expect=dagger.ReturnType.ANY,
                )
                test_output += f"+ {command}\n"

                # Some tests rely on stdout/stderr being separate
                test_output += await ctr.stdout()
                test_output += await ctr.stderr()

                if code := await ctr.exit_code():
                    error = trace.StatusCode.ERROR
                    span.set_status(error, f"command failed with exit code {code}")

    total_runtime = time.time() - start_time
    logger.info(f"Test runtime: {total_runtime:_.2f} seconds")

    if scope.cancelled_caught:
        test_output += f"\n\nTimeout error: {timeout} seconds exceeded"

    await instance.write_file(TEST_LOG_FILE, test_output)

    logger.info(
        "Test output for %s written to %s",
        instance.id,
        instance.log_dir / TEST_LOG_FILE,
    )

    if scope.cancelled_caught:
        msg = f"Test timed out after {timeout} seconds."
        raise TimeoutError(msg)

    # Get git diff after running eval script
    git_diff_output_after = await ctr.with_exec(["git", "diff"]).stdout()

    # Check if git diff changed after running eval script
    logger.info("Git diff after:\n%s", git_diff_output_after)

    if git_diff_output_after != git_diff_output_before:
        logger.info("Git diff changed after running eval script")

    return ctr


@tracer.start_as_current_span("generate report")
async def _run_report(instance: Instance, logger: Logger):
    # Get report from test output
    logger.info("Grading answer for %s...", instance.id)

    report = await to_thread.run_sync(
        functools.partial(
            get_eval_report,
            test_spec=instance.test_spec,
            prediction=instance.pred,
            test_log_path=str(instance.log_dir / TEST_LOG_FILE),
            include_tests_status=True,
        )
    )

    logger.info(
        "report: %s\nResult for %s: resolved: %s",
        report,
        instance.id,
        report[instance.id]["resolved"],
    )

    await instance.write_file(REPORT_FILE, json.dumps(report, indent=4))

    return report[instance.id]["resolved"]


def run_instances_dagger(
    predictions: dict[str, dict[str, str]],
    instances: list[SWEbenchInstance],
    full_dataset: list,
    run_id: str,
    max_workers: int,
    timeout: int,
    namespace: str = "swebench",
):
    """
    Run all instances for the given predictions on Dagger.

    Args:
        predictions (dict): Predictions dict generated by the model
        instances (list): List of instances
        full_dataset (list): List of all instances
        run_id (str): Run ID
        max_workers (int): Maximum number of workers
        timeout (int): Timeout for running tests
    """
    try:
        anyio.run(
            run_instances_dagger_async,
            predictions,
            instances,
            run_id,
            max_workers,
            timeout,
            namespace,
        )
        make_run_report(
            predictions,
            full_dataset,
            run_id,
        )
    finally:
        telemetry.shutdown()


async def run_instances_dagger_async(
    predictions: dict[str, dict[str, str]],
    instances: list[SWEbenchInstance],
    run_id: str,
    max_workers: int,
    timeout: int,
    namespace: str,
):
    """
    Run all instances for the given predictions on Dagger.

    Args:
        predictions (dict): Predictions dict generated by the model
        instances (list): List of instances
        run_id (str): Run ID
        max_workers (int): Maximum number of workers
        timeout (int): Timeout for running tests
    """

    limiter = anyio.CapacityLimiter(max_workers)

    cfg = dagger.Config(retry=None)
    cfg.console.quiet = True

    async with dagger.connection(cfg), anyio.create_task_group() as tg:
        for instance in instances:
            tg.start_soon(
                run_instance_dagger,
                instance,
                predictions[instance[KEY_INSTANCE_ID]],
                run_id,
                timeout,
                limiter,
                namespace,
            )


async def run_instance_dagger(
    bench_instance: SWEbenchInstance,
    pred: dict[str, str],
    run_id: str,
    timeout: int,
    limiter: anyio.CapacityLimiter,
    namespace: str,
):
    """
    Run a single instance with the given prediction.

    Args:
        bench_instance (SWEbenchInstance): SWE-bench instance
        pred (dict): Prediction w/ model_name_or_path, model_patch, instance_id
        run_id (str): Run ID
        timeout (int): Timeout for running tests
    """
    async with limiter:
        test_spec = await to_thread.run_sync(make_test_spec, bench_instance, namespace)
        instance = Instance(run_id, test_spec, pred)
        await instance.log_dir.mkdir(parents=True, exist_ok=True)

        logger = instance.setup_logger()

        try:
            with tracer.start_as_current_span(instance.id) as span:
                ctr = await _build_base_image(instance.test_spec)
                ctr = await _run_instance_patch(instance, ctr, logger)
                ctr = await _run_evaluation_script(instance, ctr, logger, timeout)
                resolved = await _run_report(instance, logger)

                if not resolved:
                    span.set_status(trace.StatusCode.ERROR, "not resolved")

        except Exception:
            logger.exception(
                "Error in evaluating module for %s.\nCheck %s for more information",
                instance.id,
                instance.log_dir / RUN_LOG_FILE,
            )

        finally:
            # Only write log to disk at the end to avoid too many open files
            await instance.write_file(RUN_LOG_FILE, instance.log.getvalue())

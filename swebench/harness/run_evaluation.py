from __future__ import annotations

import docker
import json
import platform
import traceback

if platform.system() == "Linux":
    import resource

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path, PurePosixPath

from swebench.image_builder.constants import CONTAINER_USER, CONTAINER_WORKDIR
from swebench.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
    CONTAINER_PATCH_FILE,
    LOG_REPORT,
    LOG_INSTANCE,
    LOG_TEST_OUTPUT,
    RUN_EVALUATION_LOG_DIR,
)
from swebench.harness.docker_utils import (
    cleanup_container,
    copy_to_container,
    exec_run_with_timeout,
)
import logging
from swebench.harness.grading import get_eval_report
from swebench.harness.reporting import make_run_report
from swebench.harness.modal_eval import (
    run_instances_modal,
    validate_modal_credentials,
)
from swebench.types import TestSpec
from swebench.harness.utils import make_test_spec
from swebench.harness.utils import (
    EvaluationError,
    load_swebench_dataset,
    get_predictions_from_file,
    run_threadpool,
    str2bool,
)
from swebench.logger import setup_logger, close_logger

GIT_APPLY_CMDS = [
    "git apply --verbose",
    "git apply --verbose --reject",
    "patch --batch --fuzz=5 -p1 -i",
]


class EvaluationError(Exception):
    def __init__(self, instance_id, message, logger):
        super().__init__(message)
        self.super_str = super().__str__()
        self.instance_id = instance_id
        self.log_path = logger.log_file
        self.logger = logger

    def __str__(self):
        return (
            f"Error in evaluation for {self.instance_id}: {self.super_str}\n"
            f"Check ({self.log_path}) for more information."
        )


def create_container(
    test_spec: TestSpec,
    client: docker.DockerClient,
    run_id: str,
    logger: logging.Logger,
):
    """
    Creates a container from an instance image for running evaluation.

    Args:
        test_spec (TestSpec): Test spec with evaluation details
        client (docker.DockerClient): Docker client for creating the container
        run_id (str): Run ID identifying process, used for the container name
        logger (logging.Logger): Logger to use for logging the creation process
    """
    container = None
    try:
        # Check if the image exists
        try:
            client.images.get(test_spec.image)
        except docker.errors.ImageNotFound:
            try:
                logger.info("Image not found locally, attempting to pull...")
                client.images.pull(test_spec.image)
            except docker.errors.ImageNotFound:
                raise EvaluationError(
                    test_spec.instance_id,
                    f"Image {test_spec.image} not found for {test_spec.instance_id}",
                    logger,
                )

        logger.info(f"Creating container for {test_spec.instance_id}...")

        container_name = f"sweb.eval.{test_spec.instance_id.lower()}.{run_id}"
        container = client.containers.create(
            image=test_spec.image,
            name=container_name,
            user=CONTAINER_USER,
            detach=True,
            command="tail -f /dev/null",
        )
        logger.info(f"Container for {test_spec.instance_id} created: {container.id}")
        return container
    except Exception as e:
        logger.error(f"Error creating container for {test_spec.instance_id}: {e}")
        logger.info(traceback.format_exc())
        cleanup_container(client, container, logger)
        raise EvaluationError(test_spec.instance_id, str(e), logger) from e


def run_instance(
    test_spec: TestSpec,
    pred: dict,
    client: docker.DockerClient,
    run_id: str,
    timeout: int | None = None,
    rewrite_reports: bool = False,
):
    """
    Run a single instance with the given prediction.

    Args:
        test_spec (TestSpec): TestSpec instance with pre-built image
        pred (dict): Prediction w/ model_name_or_path, model_patch, instance_id
        client (docker.DockerClient): Docker client
        run_id (str): Run ID
        timeout (int): Timeout for running tests
        rewrite_reports (bool): True if eval run is just to reformat existing report
    """
    # Set up logging directory
    instance_id = test_spec.instance_id
    model_name_or_path = pred.get("model_name_or_path", "None").replace("/", "__")
    log_dir = RUN_EVALUATION_LOG_DIR / run_id / model_name_or_path / instance_id

    # Set up report file
    report_path = log_dir / LOG_REPORT
    if rewrite_reports:
        test_output_path = log_dir / LOG_TEST_OUTPUT
        if not test_output_path.exists():
            raise ValueError(f"Test output file {test_output_path} does not exist")
        report = get_eval_report(
            test_spec=test_spec,
            prediction=pred,
            test_log_path=test_output_path,
            include_tests_status=True,
        )
        # Write report to report.json
        with open(report_path, "w") as f:
            f.write(json.dumps(report, indent=4))
        return instance_id, report
    if report_path.exists():
        return instance_id, json.loads(report_path.read_text())

    # Set up logger
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / LOG_INSTANCE
    logger = setup_logger(instance_id, log_file)

    # Run the instance
    container = None
    try:
        # Create container from image
        container = create_container(test_spec, client, run_id, logger)
        container.start()
        logger.info(f"Container for {instance_id} started: {container.id}")

        # Copy model prediction as patch file to container
        patch_file = Path(log_dir / "patch.diff")
        patch_file.write_text(pred["model_patch"] or "")
        logger.info(
            f"Intermediate patch for {instance_id} written to {patch_file}, now applying to container..."
        )
        copy_to_container(container, patch_file, PurePosixPath(CONTAINER_PATCH_FILE))

        # Attempt to apply patch to container (TODO: test this)
        applied_patch = False
        for git_apply_cmd in GIT_APPLY_CMDS:
            val = container.exec_run(
                f"{git_apply_cmd} {CONTAINER_PATCH_FILE}",
                workdir=CONTAINER_WORKDIR,
                user=CONTAINER_USER,
            )
            if val.exit_code == 0:
                logger.info(f"{APPLY_PATCH_PASS}:\n{val.output.decode('utf-8')}")
                applied_patch = True
                break
            else:
                logger.info(f"Failed to apply patch to container: {git_apply_cmd}")
        if not applied_patch:
            logger.info(f"{APPLY_PATCH_FAIL}:\n{val.output.decode('utf-8')}")
            raise EvaluationError(
                instance_id,
                f"{APPLY_PATCH_FAIL}:\n{val.output.decode('utf-8')}",
                logger,
            )

        # Get git diff before running eval script
        git_diff_output_before = (
            container.exec_run(
                "git -c core.fileMode=false diff", workdir=CONTAINER_WORKDIR
            )
            .output.decode("utf-8")
            .strip()
        )
        logger.info(f"Git diff before:\n{git_diff_output_before}")

        eval_file = Path(log_dir / "eval.sh")
        eval_file.write_text(test_spec.eval_script)
        logger.info(
            f"Eval script for {instance_id} written to {eval_file}; copying to container..."
        )
        copy_to_container(container, eval_file, PurePosixPath("/eval.sh"))

        # Run eval script, write output to logs
        test_output, timed_out, total_runtime = exec_run_with_timeout(
            container, "/bin/bash /eval.sh", timeout
        )
        test_output_path = log_dir / LOG_TEST_OUTPUT
        logger.info(f"Test runtime: {total_runtime:_.2f} seconds")
        with open(test_output_path, "w") as f:
            f.write(test_output)
            logger.info(f"Test output for {instance_id} written to {test_output_path}")
            if timed_out:
                f.write(f"\n\nTimeout error: {timeout} seconds exceeded.")
                raise EvaluationError(
                    instance_id,
                    f"Test timed out after {timeout} seconds.",
                    logger,
                )

        # Get git diff after running eval script (ignore permission changes)
        git_diff_output_after = (
            container.exec_run(
                "git -c core.fileMode=false diff", workdir=CONTAINER_WORKDIR
            )
            .output.decode("utf-8")
            .strip()
        )

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

        # Write report to report.json
        with open(report_path, "w") as f:
            f.write(json.dumps(report, indent=4))
        return instance_id, report
    except EvaluationError as e:
        error_msg = traceback.format_exc()
        logger.info(error_msg)
        print(e)
    except Exception as e:
        error_msg = (
            f"Error in evaluating model for {instance_id}: {e}\n"
            f"{traceback.format_exc()}\n"
            f"Check ({logger.log_file}) for more information."
        )
        logger.error(error_msg)
    finally:
        # Remove instance container + image, close logger
        cleanup_container(client, container, logger)
        close_logger(logger)
    return


def run_instances(
    predictions: dict,
    instances: list,
    max_workers: int,
    run_id: str,
    timeout: int,
    rewrite_reports: bool = False,
):
    """
    Run all instances for the given predictions in parallel.
    Expects instances to have pre-built images.

    Args:
        predictions (dict): Predictions dict generated by the model
        instances (list): List of instances with 'image' field
        max_workers (int): Maximum number of workers
        run_id (str): Run ID
        timeout (int): Timeout for running tests
        rewrite_reports (bool): True if eval run is just to reformat existing report
    """
    client = docker.from_env()
    test_specs = list(
        map(
            lambda instance: make_test_spec(instance),
            instances,
        )
    )

    # run instances in parallel
    payloads = []
    for test_spec in test_specs:
        payloads.append(
            (
                test_spec,
                predictions[test_spec.instance_id],
                client,
                run_id,
                timeout,
                rewrite_reports,
            )
        )

    # run instances in parallel
    print(f"Running {len(instances)} instances...")
    run_threadpool(run_instance, payloads, max_workers)
    print("All instances run.")


def get_dataset_from_preds(
    dataset_name: str,
    split: str,
    instance_ids: list,
    predictions: dict,
    run_id: str,
    rewrite_reports: bool,
    exclude_completed: bool = True,
):
    """
    Return only instances that have predictions and are in the dataset.
    If instance_ids is provided, only return instances with those IDs.
    If exclude_completed is True, only return instances that have not been run yet.
    """
    # load dataset
    dataset = load_swebench_dataset(dataset_name, split)
    dataset_ids = {i["instance_id"] for i in dataset}

    if instance_ids:
        # check that all instance IDs have predictions
        missing_preds = set(instance_ids) - set(predictions.keys())
        if missing_preds:
            print(
                f"Warning: Missing predictions for {len(missing_preds)} instance IDs."
            )

    # check that all prediction IDs are in the dataset
    prediction_ids = set(predictions.keys())
    if prediction_ids - dataset_ids:
        raise ValueError(
            (
                "Some prediction IDs not found in dataset!"
                f"\nMissing IDs:\n{' '.join(prediction_ids - dataset_ids)}"
            )
        )
    if instance_ids:
        dataset = [i for i in dataset if i["instance_id"] in instance_ids]

    if rewrite_reports:
        # we only return instances that have existing test outputs
        test_output_ids = set()
        for instance in dataset:
            if instance["instance_id"] not in predictions:
                continue
            prediction = predictions[instance["instance_id"]]
            test_output_file = (
                RUN_EVALUATION_LOG_DIR
                / run_id
                / prediction["model_name_or_path"].replace("/", "__")
                / prediction["instance_id"]
                / "test_output.txt"
            )
            if test_output_file.exists():
                test_output_ids.add(instance["instance_id"])
        dataset = [
            i
            for i in dataset
            if i["instance_id"] in prediction_ids
            and i["instance_id"] in test_output_ids
        ]
        return dataset

    # check which instance IDs have already been run
    completed_ids = set()
    for instance in dataset:
        if instance["instance_id"] not in prediction_ids:
            # skip instances without predictions
            continue
        prediction = predictions[instance["instance_id"]]
        report_file = (
            RUN_EVALUATION_LOG_DIR
            / run_id
            / prediction["model_name_or_path"].replace("/", "__")
            / prediction["instance_id"]
            / LOG_REPORT
        )
        if report_file.exists():
            completed_ids.add(instance["instance_id"])

    if completed_ids and exclude_completed:
        # filter dataset to only instances that have not been run
        print(f"{len(completed_ids)} instances already run, skipping...")
        dataset = [i for i in dataset if i["instance_id"] not in completed_ids]

    empty_patch_ids = {
        k
        for k, v in predictions.items()
        if v["model_patch"] == "" or v["model_patch"] is None
    }

    # filter dataset to only instances with predictions
    dataset = [
        i
        for i in dataset
        if i["instance_id"] in prediction_ids
        and i["instance_id"] not in empty_patch_ids
    ]
    return dataset


def main(
    dataset_name: str,
    split: str,
    instance_ids: list,
    predictions_path: str,
    max_workers: int,
    open_file_limit: int,
    run_id: str,
    timeout: int,
    rewrite_reports: bool,
    modal: bool,
    report_dir: str = ".",
):
    """
    Run evaluation harness for the given dataset and predictions.
    """
    if dataset_name == "SWE-bench/SWE-bench_Multimodal" and split == "test":
        print(
            "⚠️ Local evaluation for the test split of SWE-bench Multimodal is not supported. "
            "Please check out sb-cli (https://github.com/swe-bench/sb-cli/) for instructions on how to submit predictions."
        )
        return

    # set open file limit
    assert len(run_id) > 0, "Run ID must be provided"
    if report_dir is not None:
        report_dir = Path(report_dir)
        if not report_dir.exists():
            report_dir.mkdir(parents=True)

    # load predictions as map of instance_id to prediction
    predictions = get_predictions_from_file(predictions_path, dataset_name, split)
    predictions = {pred["instance_id"]: pred for pred in predictions}

    # get dataset from predictions
    dataset = get_dataset_from_preds(
        dataset_name, split, instance_ids, predictions, run_id, rewrite_reports
    )
    full_dataset = load_swebench_dataset(dataset_name, split, instance_ids)

    if modal:
        # run instances on Modal
        if not dataset:
            print("No instances to run.")
        else:
            validate_modal_credentials()
            run_instances_modal(predictions, dataset, full_dataset, run_id, timeout)
        return

    # run instances locally
    if platform.system() == "Linux":
        resource.setrlimit(resource.RLIMIT_NOFILE, (open_file_limit, open_file_limit))
    client = docker.from_env()

    if not dataset:
        print("No instances to run.")
        return make_run_report(predictions, full_dataset, run_id, client)
    else:
        # run instances (images assumed to be pre-built)
        run_instances(
            predictions,
            dataset,
            max_workers,
            run_id,
            timeout,
            rewrite_reports=rewrite_reports,
        )

    # make final report
    return make_run_report(predictions, full_dataset, run_id, client)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Run evaluation harness for the given dataset and predictions.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    # Common args
    parser.add_argument(
        "--dataset_name",
        default="SWE-bench/SWE-bench_Lite",
        type=str,
        help="Name of dataset or path to JSON file.",
    )
    parser.add_argument(
        "--split", type=str, default="test", help="Split of the dataset"
    )
    parser.add_argument(
        "--instance_ids",
        nargs="+",
        type=str,
        help="Instance IDs to run (space separated)",
    )
    parser.add_argument(
        "--predictions_path",
        type=str,
        help="Path to predictions file - if 'gold', uses gold predictions",
        required=True,
    )

    # Local execution args
    parser.add_argument(
        "--max_workers",
        type=int,
        default=4,
        help="Maximum number of workers (should be <= 75%% of CPU cores)",
    )
    parser.add_argument(
        "--open_file_limit", type=int, default=4096, help="Open file limit"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1_800,
        help="Timeout (in seconds) for running tests for each instance",
    )
    parser.add_argument(
        "--run_id", type=str, required=True, help="Run ID - identifies the run"
    )
    parser.add_argument(
        "--rewrite_reports",
        type=str2bool,
        default=False,
        help="Doesn't run new instances, only writes reports for instances with existing test outputs",
    )
    parser.add_argument(
        "--report_dir", type=str, default=".", help="Directory to write reports to"
    )

    # Modal execution args
    parser.add_argument("--modal", type=str2bool, default=False, help="Run on Modal")

    args = parser.parse_args()
    main(**vars(args))

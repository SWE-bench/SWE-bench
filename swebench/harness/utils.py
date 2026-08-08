import json
import traceback

from argparse import ArgumentTypeError
from concurrent.futures import ThreadPoolExecutor, as_completed
from datasets import Dataset, load_dataset, load_from_disk
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm
from typing import cast
from swebench.types import SWEbenchInstance, TestSpec


load_dotenv()


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


def get_predictions_from_file(predictions_path: str, dataset_name: str, split: str):
    if predictions_path == "gold":
        print("Using gold predictions - ignoring predictions_path")
        dataset = load_swebench_dataset(dataset_name, split)
        return [
            {
                "instance_id": datum["instance_id"],
                "model_patch": datum["patch"],
                "model_name_or_path": "gold",
            }
            for datum in dataset
        ]
    if predictions_path.endswith(".json"):
        with open(predictions_path, "r") as f:
            predictions = json.load(f)
            if isinstance(predictions, dict):
                predictions = list(
                    predictions.values()
                )  # compatible with SWE-agent predictions
            if not isinstance(predictions, list):
                raise ValueError(
                    "Predictions must be a list[prediction] or a dictionary[instance_id: prediction]"
                )
    elif predictions_path.endswith(".jsonl"):
        with open(predictions_path, "r") as f:
            predictions = [json.loads(line) for line in f]
    else:
        raise ValueError("Predictions path must be .json or .jsonl")

    # Validate that each prediction has an instance_id
    for pred in predictions:
        if not isinstance(pred, dict):
            raise ValueError(f"Each prediction must be a dictionary, got {type(pred)}")
        if "instance_id" not in pred:
            raise ValueError(f"Each prediction must contain '{'instance_id'}'")

    return predictions


def run_threadpool(func, payloads, max_workers):
    if max_workers <= 0:
        return run_sequential(func, payloads)
    succeeded, failed = [], []
    with tqdm(total=len(payloads), smoothing=0) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a future for running each instance
            futures = {executor.submit(func, *payload): payload for payload in payloads}
            # Wait for each future to complete
            for future in as_completed(futures):
                try:
                    # Check if instance ran successfully
                    future.result()
                    succeeded.append(futures[future])
                except Exception as e:
                    print(f"{type(e)}: {e}")
                    traceback.print_exc()
                    failed.append(futures[future])
                # Update progress bar
                pbar.update(1)
                pbar.set_description(
                    f"{len(succeeded)} ran successfully, {len(failed)} failed"
                )
    return succeeded, failed


def run_sequential(func, args_list):
    """
    Run a function with a list of arguments sequentially
    """
    succeeded, failed = [], []
    pbar = tqdm(total=len(args_list), smoothing=0)
    for args in args_list:
        try:
            func(*args)
            succeeded.append(args)
        except Exception:
            traceback.print_exc()
            failed.append(args)
        pbar.update(1)
        pbar.set_description(f"{len(succeeded)} ran successfully, {len(failed)} failed")
    pbar.close()
    return succeeded, failed


def load_swebench_dataset(
    name="SWE-bench/SWE-bench", split="test", instance_ids=None
) -> list[SWEbenchInstance]:
    """
    Load SWE-bench dataset from Hugging Face Datasets or local .json/.jsonl file
    """
    # check that all instance IDs are in the dataset
    if instance_ids:
        instance_ids = set(instance_ids)
    # Load from local file
    if name.endswith(".json"):
        dataset = json.loads(Path(name).read_text())
    elif name.endswith(".jsonl"):
        dataset = [json.loads(line) for line in Path(name).read_text().splitlines()]
    elif name.endswith(".parquet"):
        dataset = cast(Dataset, load_dataset("parquet", data_files=name, split="train"))
    else:
        # Load from Hugging Face Datasets
        if name.lower() in {"swe-bench", "swebench", "swe_bench"}:
            name = "SWE-bench/SWE-bench"
        elif name.lower() in {
            "swe-bench-lite",
            "swebench-lite",
            "swe_bench_lite",
            "swe-bench_lite",
            "lite",
        }:
            name = "SWE-bench/SWE-bench_Lite"
        parquet_path = Path(name) / f"{split}.parquet"
        if parquet_path.exists():
            dataset = cast(Dataset, load_dataset("parquet", data_files=str(parquet_path), split="train"))
        elif (Path(name) / split / "dataset_info.json").exists():
            dataset = cast(Dataset, load_from_disk(Path(name) / split))
        else:
            dataset = cast(Dataset, load_dataset(name, split=split))
    dataset_ids = {instance["instance_id"] for instance in dataset}
    if instance_ids:
        if instance_ids - dataset_ids:
            raise ValueError(
                (
                    "Some instance IDs not found in dataset!"
                    f"\nMissing IDs:\n{' '.join(instance_ids - dataset_ids)}"
                )
            )
        dataset = [
            instance for instance in dataset if instance["instance_id"] in instance_ids
        ]
    return [cast(SWEbenchInstance, instance) for instance in dataset]


def str2bool(v):
    """
    Minor helper function to convert string to boolean
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise ArgumentTypeError("Boolean value expected.")


def optional_str(value: str) -> str | None:
    """
    Convert special string values to None, otherwise return the string as-is.
    """
    if value.lower() in ("none", "null", ""):
        return None
    return value


def parse_eval_script(eval_script: str) -> list[str]:
    """Parse an eval.sh script into a command list (strip shebang + set flags)."""
    return [
        line
        for line in eval_script.strip().split("\n")
        if line not in ("#!/bin/bash", "set -uxo pipefail")
    ]


def make_test_spec(instance: dict) -> TestSpec:
    """
    Build a TestSpec from a dataset instance.

    The instance dict must contain: instance_id, image, repo, version,
    FAIL_TO_PASS, PASS_TO_PASS, log_parser, eval_type, eval_script.
    """
    f2p = instance["FAIL_TO_PASS"]
    p2p = instance["PASS_TO_PASS"]
    return TestSpec(
        instance_id=instance["instance_id"],
        image=instance["image"],
        eval_script_list=parse_eval_script(instance["eval_script"]),
        repo=instance["repo"],
        version=instance["version"],
        FAIL_TO_PASS=json.loads(f2p) if isinstance(f2p, str) else f2p,
        PASS_TO_PASS=json.loads(p2p) if isinstance(p2p, str) else p2p,
        log_parser=instance["log_parser"],
        eval_type=instance["eval_type"],
    )

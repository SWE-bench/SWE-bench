import json
import re
import requests
import traceback

from argparse import ArgumentTypeError
from concurrent.futures import ThreadPoolExecutor, as_completed
from datasets import Dataset, load_dataset, load_from_disk
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm
from typing import cast, Union
from swebench.types import SWEbenchInstance, TestSpec


load_dotenv()


# Import here to avoid circular import
def get_eval_script_list(instance: SWEbenchInstance, dataset_name: str) -> list[str]:
    from swebench.harness.eval_script_gen import (
        get_eval_script_list as _get_eval_script_list,
    )

    return _get_eval_script_list(instance, dataset_name)


class EvaluationError(Exception):
    def __init__(self, instance_id, message, logger):
        super().__init__(message)
        self.instance_id = instance_id
        self.log_file = logger.log_file
        self.logger = logger

    def __str__(self):
        log_msg = traceback.format_exc()
        self.logger.info(log_msg)
        return (
            f"{self.instance_id}: {super().__str__()}\n"
            f"Check ({self.log_file}) for more information."
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
    # Load from local .json/.jsonl file
    if name.endswith(".json"):
        dataset = json.loads(Path(name).read_text())
    elif name.endswith(".jsonl"):
        dataset = [json.loads(line) for line in Path(name).read_text().splitlines()]
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
        if (Path(name) / split / "dataset_info.json").exists():
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


### MARK - Patch Correction
PATCH_PATTERN = re.compile(
    r"(?:diff[\w\_\.\ \/\-]+\n)?\-\-\-\s+a\/(?:.*?)\n\+\+\+\s+b\/(?:.*?)(?=diff\ |\-\-\-\ a\/|\Z)",
    re.DOTALL,
)
PATCH_FILE_PATTERN = re.compile(r"\-\-\-\s+a\/(?:.+)\n\+\+\+\s+b\/(?:.+)")
PATCH_HUNK_PATTERN = re.compile(
    r"\@\@\s+\-(\d+),(\d+)\s+\+(\d+),(\d+)\s+\@\@(.+?)(?=diff\ |\-\-\-\ a\/|\@\@\ \-|\Z)",
    re.DOTALL,
)


def get_first_idx(charlist):
    """Get index of first occurrence of "-" or "+" in charlist"""
    first_min = charlist.index("-") if "-" in charlist else len(charlist)
    first_plus = charlist.index("+") if "+" in charlist else len(charlist)
    return min(first_min, first_plus)


def get_last_idx(charlist):
    """Get index of last occurrence of "-" or "+" in charlist"""
    char_idx = get_first_idx(charlist[::-1])
    last_idx = len(charlist) - char_idx
    return last_idx + 1


def strip_content(hunk):
    """Remove trailing non +/- lines and trailing whitespace per line per hunk"""
    first_chars = list(map(lambda x: None if not len(x) else x[0], hunk.split("\n")))
    first_idx = get_first_idx(first_chars)
    last_idx = get_last_idx(first_chars)
    new_lines = list(map(lambda x: x.rstrip(), hunk.split("\n")[first_idx:last_idx]))
    # should leave one space for empty context lines
    new_lines = [line if line.strip() else " " for line in new_lines]
    new_hunk = "\n" + "\n".join(new_lines) + "\n"
    return new_hunk, first_idx - 1


def get_hunk_stats(pre_start, pre_len, post_start, post_len, hunk, total_delta):
    """Recalculate hunk start/end position and diff delta"""
    stats = {"context": 0, "added": 0, "subtracted": 0}
    hunk = hunk.split("\n", 1)[-1].strip("\n")
    for line in hunk.split("\n"):
        if line.startswith("-"):
            stats["subtracted"] += 1
        elif line.startswith("+"):
            stats["added"] += 1
        else:
            stats["context"] += 1
    context = stats["context"]
    added = stats["added"]
    subtracted = stats["subtracted"]
    pre_len = context + subtracted
    post_start = pre_start + total_delta
    post_len = context + added
    total_delta = total_delta + (post_len - pre_len)
    return pre_start, pre_len, post_start, post_len, total_delta


def extract_minimal_patch(model_patch):
    """
    Wrapper function that takes hunk and
    * Removes trailing non +/- lines and trailing whitespace per line per hunk
    * Recalculates hunk start/end position and diff delta
    * Returns new patch
    """
    model_patch = model_patch.lstrip("\n")
    new_patch = ""
    for patch in PATCH_PATTERN.findall(model_patch):
        total_delta = 0
        patch_header = PATCH_FILE_PATTERN.findall(patch)[0]
        if patch_header:
            new_patch += patch_header + "\n"
        for hunk in PATCH_HUNK_PATTERN.findall(patch):
            pre_start, pre_len, post_start, post_len, content = hunk
            pre_start, pre_len, post_start, post_len, content = list(
                map(lambda x: int(x) if x.isnumeric() else x, hunk)
            )
            content, adjust_pre_start = strip_content(content)
            pre_start += adjust_pre_start
            pre_start, pre_len, post_start, post_len, total_delta = get_hunk_stats(
                pre_start, pre_len, post_start, post_len, content, total_delta
            )
            new_patch += (
                f"@@ -{pre_start},{pre_len} +{post_start},{post_len} @@{content}"
            )
    return new_patch


def has_attribute_or_import_error(log_before):
    """
    Check to see if Attribute/Import-prefix is in log text

    Args:
        log_before (str): Validation log text before patch application
    """
    log_before = log_before.lower()

    if any([x in log_before for x in ["attribute", "import"]]):

        def get_lines_with_word(text, target_word):
            # Function to extract line(s) that contains target_word
            text, target_word = text.lower(), target_word.lower()
            lines, hits = text.split("\n")[::-1], []
            for line in lines:
                if target_word in line:
                    hits.append(line)
            return hits

        # Get line with Attribute/Import error
        lines_1 = get_lines_with_word(log_before, "attribute")
        lines_2 = get_lines_with_word(log_before, "import")
        lines_1 = " ".join(lines_1)
        lines_2 = " ".join(lines_2)

        if any([(x in lines_1 or x in lines_2) for x in ["error", "fail"]]):
            return True
    return False


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


def get_repo_file(repo, commit, filepath):
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{filepath}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None


def get_test_specs_from_dataset(
    dataset: Union[list[SWEbenchInstance], list[TestSpec]],
) -> list[TestSpec]:
    """
    Idempotent function that converts a list of SWEbenchInstance objects to a list of TestSpec objects.
    """
    if isinstance(dataset[0], TestSpec):
        return cast(list[TestSpec], dataset)
    return list(
        map(
            lambda x: make_test_spec(
                x, dataset_name="SWE-bench/SWE-bench_Verified"
            ),  # Default for backward compatibility
            cast(list[SWEbenchInstance], dataset),
        )
    )


def make_test_spec(
    instance: SWEbenchInstance,
    dataset_name: str = "SWE-bench/SWE-bench_Verified",  # Default for backward compatibility
) -> TestSpec:
    """
    Create a TestSpec from a SWEbenchInstance for evaluation purposes.
    Expects the instance to have an 'image' field pointing to a pre-built Docker image.
    """
    if isinstance(instance, TestSpec):
        return instance

    instance_id = instance["instance_id"]
    repo = instance["repo"]
    version = instance.get("version")
    base_commit = instance["base_commit"]
    test_patch = instance["test_patch"]

    if "image" not in instance:
        raise ValueError(f"Instance {instance_id} missing required 'image' field")
    image = instance["image"]

    def _from_json_or_obj(key: str) -> Union[dict, list]:
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
    specs = get_data_spec(repo, version)

    eval_script_list = get_eval_script_list(instance, dataset_name)

    return TestSpec(
        instance_id=instance_id,
        image=image,
        eval_script_list=eval_script_list,
        repo=repo,
        version=version,
        FAIL_TO_PASS=fail_to_pass,
        PASS_TO_PASS=pass_to_pass,
    )

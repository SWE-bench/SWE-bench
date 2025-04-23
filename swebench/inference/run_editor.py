#!/usr/bin/env python3

import docker
import os
import tempfile
import subprocess
import json
from typing import List
from argparse import ArgumentParser
import logging
import shutil
from tqdm import tqdm
from swebench.inference.prepare_utils import prepare_output, prepare_input
from swebench.inference.make_datasets.create_instance import PROMPT_FUNCTIONS


logger = logging.getLogger(__name__)

def github_repo_url(repo: str) -> str:
    return f"https://github.com/{repo}"

def clone_repo(url: str, commit: str) -> str:
    temp_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(temp_dir, "repo")
    os.makedirs(repo_dir, exist_ok=True)
    subprocess.run(["git", "clone", url, repo_dir])
    subprocess.run(["git", "checkout", commit], cwd=repo_dir)
    return repo_dir

def make_prompt(datum) -> str:
    premise = "You will be provided an issue statement explaining a problem to resolve. You can read any files in the repository to help you solve the issue."
    issue = datum["problem_statement"]
    final_instruction = (
        "I need you to solve the provided issue."
        + "You can read any files in the repository and execute any commands."
        + "You can't ask me for any information, you must solve the issue by yourself."
        + "If you will try to ask me anything, the task will be failed."
        + "Please solve this issue by editing any files in the repository."
        + "After you solve the issue, run command `touch /tmp/request_finished` to finish the task."
    )
    final_text = [
        premise,
        "<issue>",
        issue,
        "</issue>",
        "",
        final_instruction,
    ]
    return "\n".join(final_text)

def run_container(
    image_name : str,
    repo_dir : str,
    files : List[str],
    prompt : str,
):
    client = docker.from_env()
    client.containers.run(
        image_name, 
        volumes={repo_dir: {"bind": "/home/vscode/repo", "mode": "rw"}},
        environment={"PROMPT": prompt, "FILES": ",".join(files)},
        ports={'5900/tcp': 5901}
    )

def get_diff(repo_dir: str) -> str:
    with open(os.path.join(repo_dir, "diff.patch")) as f:
        return f.read()

def main(
    image_name,
    dataset_name_or_path,
    split,
    shard_id,
    num_shards,
    output_dir,
):
    if shard_id is None and num_shards is not None:
        logger.warning(
            f"Received num_shards={num_shards} but shard_id is None, ignoring"
        )
    if shard_id is not None and num_shards is None:
        logger.warning(f"Received shard_id={shard_id} but num_shards is None, ignoring")
    
    output_file, existing_ids = prepare_output(
        dataset_name_or_path=dataset_name_or_path,
        split=split,
        shard_id=shard_id,
        num_shards=num_shards,
        output_dir=output_dir,
        image_name=image_name,
    )
    
    dataset = prepare_input(
        dataset_name_or_path=dataset_name_or_path,
        split=split,
        existing_ids=existing_ids,
        shard_id=shard_id,
        num_shards=num_shards,
    )

    # for datum in tqdm(dataset, desc=f"Inference for {image_name}"):
    datum = dataset[0]
    # TODO: timeout
    repo_dir = clone_repo(github_repo_url(datum["repo"]), datum["environment_setup_commit"] or datum["base_commit"])
    run_container(
        image_name=image_name,
        repo_dir=repo_dir,
        files=[], # TODO: not yet implemented
        prompt=make_prompt(datum),
    )
    diff = get_diff(repo_dir)
    print('-' * 100)
    print(diff)
    print('-' * 100)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--image_name",
        type=str,
        required=True,
        help="Name of image.",
    )
    parser.add_argument(
        "--dataset_name_or_path",
        type=str,
        required=True,
        help="HuggingFace dataset name or local path",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to use",
    )
    parser.add_argument(
        "--shard_id",
        type=int,
        default=None,
        help="Shard id to process. If None, process all shards.",
    )
    parser.add_argument(
        "--num_shards",
        type=int,
        default=None,
        help="Number of shards. If None, process all shards.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        required=True,
        help="Path to the output file.",
    )
    args = parser.parse_args()
    main(**vars(args))

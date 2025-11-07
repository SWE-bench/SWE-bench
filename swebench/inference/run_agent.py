#!/usr/bin/env python3
# python -m swebench.harness.run_evaluation --dataset_name output.jsonl --predictions_path preds.jsonl --namespace '' --run_id stuff --repo_specs_override specs.json --repo_ext_override exts.json
"""
Script for running inference on SWE-bench using locally installed coding agents.

This script runs coding agents inside Docker containers (the same ones used for evaluation),
iterates over a dataset, and runs the agent on each task instance.

Usage:
    python -m swebench.inference.run_agent \
        --dataset_name dataset.jsonl \
        --agent_name claude \
        --agent_command 'prompt="$(cat $PROBLEM_STATEMENT)" ; claude --permission-mode bypassPermissions "$prompt"' \
        --output_dir ./agent_results \
        --max_workers 1 \
        --namespace '' \
        --repo_specs_override specs.json \
        --repo_ext_override exts.json
"""

import json
import logging
import os
import tempfile
import traceback
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional

import docker
from tqdm.auto import tqdm

from swebench.harness.constants import (
    DOCKER_USER,
    DOCKER_WORKDIR,
    DEFAULT_DOCKER_SPECS,
    KEY_INSTANCE_ID,
    KEY_MODEL,
    KEY_PREDICTION,
    MAP_REPO_TO_EXT,
    MAP_REPO_VERSION_TO_SPECS,
    RUN_EVALUATION_LOG_DIR,
    UTF8,
)
from swebench.harness.docker_build import build_container, build_env_images, setup_logger
from swebench.harness.docker_utils import copy_to_container, cleanup_container
from swebench.harness.test_spec.test_spec import make_test_spec, TestSpec
from swebench.harness.utils import EvaluationError, load_swebench_dataset
from swebench.inference.make_datasets.utils import extract_diff

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_agent_on_instance(
    test_spec: TestSpec,
    instance: Dict,
    agent_name: str,
    agent_command: str,
    client: docker.DockerClient,
    run_id: str,
    timeout: int = 1800,
    force_rebuild: bool = False,
    agents_md: Optional[str] = None,
) -> Dict:
    """
    Run the coding agent on a single instance.
    
    Args:
        test_spec (TestSpec): Test specification for the instance
        instance (Dict): The dataset instance containing problem_statement etc.
        agent_command (str): Command template to run the agent with $PROBLEM_STATEMENT placeholder
        client (docker.DockerClient): Docker client
        run_id (str): Run ID for container naming
        timeout (int): Timeout in seconds for agent execution
        force_rebuild (bool): Whether to force rebuild container images
        agents_md (Optional[str]): Path to file to copy as AGENTS.md in container
        
    Returns:
        Dict: Result containing instance_id, model_patch, and metadata
    """
    instance_id = instance[KEY_INSTANCE_ID]
    
    # Set up logging
    log_dir = RUN_EVALUATION_LOG_DIR / run_id / instance_id
    log_dir.mkdir(parents=True, exist_ok=True)
    logger_instance = setup_logger(instance_id, log_dir / "run_agent.log")
    
    container = None
    try:
        logger_instance.info(f"Starting agent run for {instance_id}")
        
        # Build and start container
        container = build_container(
            test_spec, client, run_id, logger_instance, nocache=False, force_rebuild=force_rebuild
        )
        container.start()
        logger_instance.info(f"Container for {instance_id} started: {container.id}")
        
        # Create problem statement file in container
        problem_statement = instance.get("problem_statement", "")
        problem_file_path = "/tmp/problem_statement.txt"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(problem_statement)
            tmp_file_path = tmp_file.name
        
        try:
            # Copy problem statement to container
            copy_to_container(container, Path(tmp_file_path), PurePosixPath(problem_file_path))
            logger_instance.info(f"Problem statement copied to container at {problem_file_path}")
            
            # Copy agents_md file to container if provided
            if agents_md:
                agents_md_path = Path(agents_md)
                if not agents_md_path.exists():
                    logger_instance.warning(f"AGENTS.md file not found: {agents_md}")
                else:
                    container_agents_md_path = PurePosixPath(DOCKER_WORKDIR) / "AGENTS.md"
                    copy_to_container(container, agents_md_path, container_agents_md_path)
                    logger_instance.info(f"AGENTS.md file copied to container at {container_agents_md_path}")
                    
                    container_claude_md_path = PurePosixPath(DOCKER_WORKDIR) / "CLAUDE.md"
                    copy_to_container(container, agents_md_path, container_claude_md_path)
                    logger_instance.info(f"AGENTS.md file copied to container at {container_claude_md_path}")
            
            # Replace $PROBLEM_STATEMENT placeholder in agent command
            actual_command = agent_command.replace("$PROBLEM_STATEMENT", problem_file_path)
            logger_instance.info(f"Running agent command: {actual_command}")
            
            # Execute the agent command in the container
            result = container.exec_run(
                cmd=f"bash -c 'source /root/.nvm/nvm.sh && export IS_SANDBOX=1 {actual_command}'",
                workdir=DOCKER_WORKDIR,
                user=DOCKER_USER,
                stream=False,
                demux=True,
            )
            
            if result.exit_code == 0:
                logger_instance.info("Agent command completed successfully")
                stdout = result.output[0].decode(UTF8) if result.output[0] else ""
                stderr = result.output[1].decode(UTF8) if result.output[1] else ""
                agent_output = stdout + stderr
            else:
                logger_instance.error(f"Agent command failed with exit code {result.exit_code}")
                stdout = result.output[0].decode(UTF8) if result.output[0] else ""
                stderr = result.output[1].decode(UTF8) if result.output[1] else ""
                agent_output = stdout + stderr
                logger_instance.error(f"Agent output: {agent_output}")
                
            # Get git diff to see what changes the agent made
            git_diff_result = container.exec_run(
                'bash -c "git add -N . && git -c core.fileMode=false diff -- . \':(exclude)swebench/\'"',
                workdir=DOCKER_WORKDIR,
                user=DOCKER_USER
            )
            
            if git_diff_result.exit_code == 0:
                model_patch = git_diff_result.output.decode(UTF8).strip()
                logger_instance.info(f"Git diff from agent:\n{model_patch}")
            else:
                model_patch = ""
                logger_instance.warning("Failed to get git diff")
                
            logger_instance.info(f"Extracted patch length: {len(model_patch)} chars")
            
            return {
                KEY_INSTANCE_ID: instance_id,
                KEY_PREDICTION: model_patch,
                KEY_MODEL: agent_name,
                "agent_command": actual_command,
                "agent_output": agent_output,
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        error_msg = f"Error running agent on {instance_id}: {str(e)}"
        logger_instance.error(error_msg)
        logger_instance.error(traceback.format_exc())
        
        return {
            KEY_INSTANCE_ID: instance_id,
            KEY_PREDICTION: "",
            KEY_MODEL: agent_name,
            "error": error_msg,
        }
        
    finally:
        # Clean up container
        if container:
            try:
                container.stop()
                container.remove()
                logger_instance.info(f"Container {container.id} cleaned up")
            except Exception as e:
                logger_instance.warning(f"Failed to clean up container: {e}")


def run_agent_inference(
    dataset: List[Dict],
    agent_name: str,
    agent_command: str,
    output_file: Path,
    max_workers: int = 1,
    timeout: int = 1800,
    force_rebuild: bool = False,
    namespace: Optional[str] = None,
    instance_image_tag: str = "latest",
    env_image_tag: str = "latest",
    existing_ids: Optional[set] = None,
    agents_md: Optional[str] = None,
) -> None:
    """
    Run agent inference on the entire dataset.
    
    Args:
        dataset (List[Dict]): List of dataset instances
        agent_name (str): Name of the agent
        agent_command (str): Command template to run the agent
        output_file (Path): File to write results to
        max_workers (int): Maximum number of parallel workers
        timeout (int): Timeout per instance in seconds
        force_rebuild (bool): Whether to force rebuild images
        namespace (Optional[str]): Docker namespace for images
        instance_image_tag (str): Tag for instance images
        env_image_tag (str): Tag for environment images
        existing_ids (Optional[set]): Set of already processed instance IDs
        agents_md (Optional[str]): Path to file to copy as AGENTS.md in container
    """
    if existing_ids is None:
        existing_ids = set()
        
    # Filter out already processed instances
    filtered_dataset = [
        instance for instance in dataset 
        if instance[KEY_INSTANCE_ID] not in existing_ids
    ]
    
    if not filtered_dataset:
        logger.info("No instances to process")
        return
        
    logger.info(f"Processing {len(filtered_dataset)} instances with {max_workers} workers")
    
    # Create test specs for all instances
    test_specs = []
    for instance in filtered_dataset:
        test_spec = make_test_spec(
            instance,
            namespace=namespace,
            instance_image_tag=instance_image_tag,
            env_image_tag=env_image_tag,
        )
        test_specs.append((test_spec, instance))
    
    client = docker.from_env()
    run_id = Path(output_file).stem
    
    # Build environment images first (same as run_evaluation.py)
    if namespace is None:
        logger.info("Building environment images...")
        build_env_images(
            client,
            filtered_dataset,
            force_rebuild,
            max_workers,
            namespace,
            instance_image_tag,
            env_image_tag,
        )
        logger.info("Environment images built successfully")
    
    # Process instances
    with open(output_file, "a") as f:
        if max_workers == 1:
            # Sequential processing
            for test_spec, instance in tqdm(test_specs, desc="Processing instances"):
                result = run_agent_on_instance(
                    test_spec, instance, agent_name, agent_command, client, run_id, 
                    timeout=timeout, force_rebuild=force_rebuild, agents_md=agents_md
                )
                print(json.dumps(result), file=f, flush=True)
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for test_spec, instance in test_specs:
                    future = executor.submit(
                        run_agent_on_instance,
                        test_spec, instance, agent_name, agent_command, client, run_id,
                        timeout, force_rebuild, agents_md
                    )
                    futures[future] = instance[KEY_INSTANCE_ID]
                
                for future in tqdm(as_completed(futures), total=len(futures), desc="Processing instances"):
                    try:
                        result = future.result()
                        print(json.dumps(result), file=f, flush=True)
                    except Exception as e:
                        instance_id = futures[future]
                        logger.error(f"Failed to process {instance_id}: {e}")
                        error_result = {
                            KEY_INSTANCE_ID: instance_id,
                            KEY_PREDICTION: "",
                            KEY_MODEL: agent_name,
                            "error": str(e),
                        }
                        print(json.dumps(error_result), file=f, flush=True)


def main(
    dataset_name: str,
    split: str,
    agent_name: str,
    agent_command: str,
    output_dir: str,
    max_workers: int = 1,
    timeout: int = 1800,
    force_rebuild: bool = False,
    namespace: Optional[str] = None,
    instance_image_tag: str = "latest",
    env_image_tag: str = "latest",
    instance_ids: Optional[List[str]] = None,
    repo_specs_override: Optional[str] = None,
    repo_ext_override: Optional[str] = None,
    agents_md: Optional[str] = None,
):
    """
    Main function to run agent inference on SWE-bench dataset.
    """
    # Validate agent command has the required placeholder
    if "$PROBLEM_STATEMENT" not in agent_command:
        raise ValueError("Agent command must contain $PROBLEM_STATEMENT placeholder")
    
    # Load repo specs override if provided
    if repo_specs_override:
        try:
            with open(repo_specs_override, 'r') as f:
                override_specs = json.load(f)
            
            # Update the global MAP_REPO_VERSION_TO_SPECS with override data
            MAP_REPO_VERSION_TO_SPECS.update(override_specs)
            logger.info(f"Loaded repository specification overrides from {repo_specs_override}")
            logger.info(f"Updated specifications for {len(override_specs)} repositories")
        except FileNotFoundError:
            raise ValueError(f"Repository specs override file not found: {repo_specs_override}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in repository specs override file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading repository specs override file: {e}")

    # Load repo extension override if provided
    if repo_ext_override:
        try:
            with open(repo_ext_override, 'r') as f:
                override_exts = json.load(f)
            
            # Update the global MAP_REPO_TO_EXT with override data
            MAP_REPO_TO_EXT.update(override_exts)
            logger.info(f"Loaded repository extension overrides from {repo_ext_override}")
            logger.info(f"Updated extensions for {len(override_exts)} repositories")
        except FileNotFoundError:
            raise ValueError(f"Repository extension override file not found: {repo_ext_override}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in repository extension override file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading repository extension override file: {e}")
    
    # Load dataset
    logger.info(f"Loading dataset {dataset_name}, split {split}")
    dataset = load_swebench_dataset(dataset_name, split, instance_ids)
    logger.info(f"Loaded {len(dataset)} instances")
    
    # Set up output file
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_nickname = dataset_name.split('/')[-1] if '/' in dataset_name else dataset_name
    output_file = output_dir / f"{agent_name}__{dataset_nickname}__{split}.jsonl"
    
    # Check for existing results
    existing_ids = set()
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    existing_ids.add(data[KEY_INSTANCE_ID])
                except (json.JSONDecodeError, KeyError):
                    continue
        logger.info(f"Found {len(existing_ids)} already processed instances")
    
    # Run agent inference
    run_agent_inference(
        dataset=dataset,
        agent_name=agent_name,
        agent_command=agent_command,
        output_file=output_file,
        max_workers=max_workers,
        timeout=timeout,
        force_rebuild=force_rebuild,
        namespace=namespace,
        instance_image_tag=instance_image_tag,
        env_image_tag=env_image_tag,
        existing_ids=existing_ids,
        agents_md=agents_md,
    )
    
    logger.info(f"Agent inference completed. Results written to {output_file}")


if __name__ == "__main__":
    if "anthropic_api_key" not in DEFAULT_DOCKER_SPECS:
        raise ValueError("ANTHROPIC_API_KEY is not set in the environment")

    parser = ArgumentParser(
        description=__doc__,
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "--dataset_name",
        type=str,
        required=True,
        help="Name of the dataset (HuggingFace dataset or local path)",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to use",
    )
    parser.add_argument(
        "--agent_name",
        type=str,
        required=True,
        help="Name of the agent",
    )
    parser.add_argument(
        "--agent_command",
        type=str,
        required=True,
        help="Command to run the agent. Use $PROBLEM_STATEMENT as placeholder for problem statement file path",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./agent_results",
        help="Directory to write results to",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=1,
        help="Maximum number of parallel workers",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout per instance in seconds",
    )
    parser.add_argument(
        "--force_rebuild",
        action="store_true",
        help="Force rebuild of Docker images",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default=None,
        help="Docker namespace for images",
    )
    parser.add_argument(
        "--instance_image_tag",
        type=str,
        default="latest",
        help="Tag for instance Docker images",
    )
    parser.add_argument(
        "--env_image_tag",
        type=str,
        default="latest",
        help="Tag for environment Docker images",
    )
    parser.add_argument(
        "--instance_ids",
        nargs="*",
        type=str,
        help="Specific instance IDs to process (if not provided, processes all)",
    )
    parser.add_argument(
        "--repo_specs_override",
        type=str,
        help="Path to JSON file containing repository specification overrides for MAP_REPO_VERSION_TO_SPECS"
    )
    parser.add_argument(
        "--repo_ext_override",
        type=str,
        help="Path to JSON file containing repository extension overrides for MAP_REPO_TO_EXT"
    )
    parser.add_argument(
        "--agents_md",
        type=str,
        help="Path to a file to copy into the container as AGENTS.md"
    )
    
    args = parser.parse_args()
    
    main(
        dataset_name=args.dataset_name,
        split=args.split,
        agent_name=args.agent_name,
        agent_command=args.agent_command,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        timeout=args.timeout,
        force_rebuild=args.force_rebuild,
        namespace=args.namespace,
        instance_image_tag=args.instance_image_tag,
        env_image_tag=args.env_image_tag,
        instance_ids=args.instance_ids,
        repo_specs_override=args.repo_specs_override,
        repo_ext_override=args.repo_ext_override,
        agents_md=args.agents_md,
    )


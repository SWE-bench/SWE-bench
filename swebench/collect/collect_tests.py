#!/usr/bin/env python3

"""
Script to collect FAIL_TO_PASS and PASS_TO_PASS tests for SWE-bench instances.

This script:
1. Clones the repository at the base commit
2. Runs tests and collects results (before patch)
3. Applies the patch
4. Runs tests again and collects results (after patch)
5. Compares results to determine FAIL_TO_PASS and PASS_TO_PASS tests
6. Updates the dataset JSON file with the test lists
"""

import argparse
import docker
import json
import logging
import tempfile
import threading
from pathlib import Path, PurePosixPath
from tqdm.auto import tqdm
from typing import Dict, List, Set, Tuple, Optional

from swebench.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
    DOCKER_PATCH,
    DOCKER_USER,
    DOCKER_WORKDIR,
    MAP_REPO_VERSION_TO_SPECS,
    TestStatus,
    UTF8,
)
from swebench.harness.docker_build import (
    BuildImageError,
    build_container,
    build_env_images,
    close_logger,
    setup_logger,
)
from swebench.harness.docker_utils import (
    cleanup_container,
    copy_to_container,
    exec_run_with_timeout,
)
from swebench.harness.log_parsers.kotlin import parse_log_gradle
from swebench.harness.test_spec.test_spec import make_test_spec, TestSpec
from swebench.harness.utils import EvaluationError, run_threadpool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

GIT_APPLY_CMDS = [
    "git apply --verbose",
    "git apply --verbose --reject",
    "patch --batch --fuzz=5 -p1 -i",
]


class TestResult:
    """Represents the result of a test execution."""
    
    def __init__(self):
        self.passed: Set[str] = set()
        self.failed: Set[str] = set()
        self.skipped: Set[str] = set()
        self.errors: Set[str] = set()
    
    def all_tests(self) -> Set[str]:
        """Return all test names."""
        return self.passed | self.failed | self.skipped | self.errors
    
    @staticmethod
    def from_status_map(status_map: Dict[str, str]) -> 'TestResult':
        """
        Create TestResult from a status map (output of parse_log_gradle).
        
        Args:
            status_map: Dictionary mapping test names to status strings
            
        Returns:
            TestResult object
        """
        result = TestResult()
        for test_name, status in status_map.items():
            if status == TestStatus.PASSED.value:
                result.passed.add(test_name)
            elif status == TestStatus.FAILED.value:
                result.failed.add(test_name)
            elif status == TestStatus.ERROR.value:
                result.errors.add(test_name)
            elif status == TestStatus.SKIPPED.value:
                result.skipped.add(test_name)
        return result


def run_tests_in_container(
    container,
    test_spec: TestSpec,
    patch_content: Optional[str],
    logger,
    timeout: int = 1800,
) -> Optional[TestResult]:
    """
    Run tests in a container, optionally applying a patch first.
    
    Args:
        container: Docker container instance
        test_spec: TestSpec object
        patch_content: Patch content to apply (None for no patch)
        logger: Logger instance
        timeout: Timeout for test execution
        
    Returns:
        TestResult object or None on failure
    """
    try:
        # Apply patch if provided
        if patch_content and patch_content.strip():
            # Write patch to temporary file
            patch_file = Path(tempfile.mktemp(suffix=".diff"))
            patch_file.write_text(patch_content)
            
            # Copy patch to container
            copy_to_container(container, patch_file, PurePosixPath(DOCKER_PATCH))
            patch_file.unlink()
            
            # Try to apply patch
            applied_patch = False
            for git_apply_cmd in GIT_APPLY_CMDS:
                val = container.exec_run(
                    f"{git_apply_cmd} {DOCKER_PATCH}",
                    workdir=DOCKER_WORKDIR,
                    user=DOCKER_USER,
                )
                if val.exit_code == 0:
                    logger.info(f"{APPLY_PATCH_PASS}:\n{val.output.decode(UTF8)}")
                    applied_patch = True
                    break
                else:
                    logger.info(f"Failed to apply patch: {git_apply_cmd}")
            
            if not applied_patch:
                logger.error(f"{APPLY_PATCH_FAIL}:\n{val.output.decode(UTF8)}")
                return None
        
        # Create and copy eval script to container
        eval_file = Path(tempfile.mktemp(suffix=".sh"))
        eval_file.write_text(test_spec.eval_script)
        copy_to_container(container, eval_file, PurePosixPath("/eval.sh"))
        eval_file.unlink()
        
        # Run tests
        logger.info("Running tests in container...")
        test_output, timed_out, total_runtime = exec_run_with_timeout(
            container, "/bin/bash /eval.sh", timeout
        )
        logger.info(f"Test runtime: {total_runtime:_.2f} seconds")
        
        if timed_out:
            logger.error(f"Tests timed out after {timeout} seconds")
            return None
        
        # Parse test output
        logger.info("Parsing test output...")
        status_map = parse_log_gradle(test_output, test_spec)
        
        if not status_map:
            logger.warning("No tests found in output")
            return TestResult()
        
        # Convert status map to TestResult
        result = TestResult.from_status_map(status_map)
        
        logger.info(f"Parsed {len(result.all_tests())} tests")
        logger.info(f"  Passed: {len(result.passed)}, Failed: {len(result.failed)}, "
                   f"Errors: {len(result.errors)}, Skipped: {len(result.skipped)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error running tests in container: {e}")
        import traceback
        traceback.print_exc()
        return None


def collect_tests_for_instance(
    instance: dict,
    client: docker.DockerClient,
    run_id: str,
    force_rebuild: bool = False,
    timeout: int = 1800,
) -> Tuple[List[str], List[str]]:
    """
    Collect FAIL_TO_PASS and PASS_TO_PASS tests for a single instance using Docker containers.
    
    Args:
        instance: Instance dictionary from dataset
        client: Docker client
        run_id: Run ID for container naming
        force_rebuild: Whether to force rebuild images
        timeout: Timeout for test execution
        
    Returns:
        Tuple of (FAIL_TO_PASS list, PASS_TO_PASS list)
    """
    instance_id = instance['instance_id']
    patch = instance['patch']
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing instance: {instance_id}")
    logger.info(f"{'='*80}")
    
    # Create TestSpec for this instance
    test_spec = make_test_spec(instance)
    
    # Set up logging
    log_dir = Path(tempfile.mkdtemp(prefix=f"collect_tests_{instance_id}_"))
    log_file = log_dir / "collect_tests.log"
    instance_logger = setup_logger(f"{instance_id}_collect", log_file)
    
    container = None
    try:
        # Build and start container (without patch)
        instance_logger.info(f"Building container for {instance_id}...")
        container = build_container(
            test_spec, client, run_id, instance_logger, nocache=False, force_rebuild=force_rebuild
        )
        container.start()
        instance_logger.info(f"Container started: {container.id}")
        
        # Run tests BEFORE patch
        instance_logger.info("Running tests BEFORE patch...")
        before_result = run_tests_in_container(
            container, test_spec, None, instance_logger, timeout
        )
        
        if before_result is None:
            instance_logger.error(f"Failed to run tests before patch for {instance_id}")
            return [], []
        
        # Stop and remove the container to reset state
        instance_logger.info("Stopping container to reset state...")
        container.stop()
        container.remove(v=True)
        
        # Build and start a fresh container for after-patch tests
        instance_logger.info("Starting fresh container for after-patch tests...")
        container = build_container(
            test_spec, client, run_id, instance_logger, nocache=False, force_rebuild=False
        )
        container.start()
        instance_logger.info(f"Container started: {container.id}")
        
        # Run tests AFTER patch
        instance_logger.info("Running tests AFTER patch...")
        after_result = run_tests_in_container(
            container, test_spec, patch, instance_logger, timeout
        )
        
        if after_result is None:
            instance_logger.error(f"Failed to run tests after patch for {instance_id}")
            return [], []
        
        # Determine FAIL_TO_PASS and PASS_TO_PASS
        # FAIL_TO_PASS: tests that failed/errored before but passed after
        before_failing = before_result.failed | before_result.errors
        fail_to_pass = sorted(list(before_failing & after_result.passed))
        
        # PASS_TO_PASS: tests that passed both before and after
        pass_to_pass = sorted(list(before_result.passed & after_result.passed))
        
        instance_logger.info(f"\nResults for {instance_id}:")
        instance_logger.info(f"  FAIL_TO_PASS: {len(fail_to_pass)} tests")
        instance_logger.info(f"  PASS_TO_PASS: {len(pass_to_pass)} tests")
        
        if fail_to_pass:
            instance_logger.info(f"  Sample FAIL_TO_PASS: {fail_to_pass[:3]}")
        if pass_to_pass:
            instance_logger.info(f"  Sample PASS_TO_PASS: {pass_to_pass[:3]}")
        
        return fail_to_pass, pass_to_pass
        
    except (EvaluationError, BuildImageError) as e:
        instance_logger.error(f"Error processing {instance_id}: {e}")
        import traceback
        traceback.print_exc()
        return [], []
    except Exception as e:
        instance_logger.error(f"Unexpected error processing {instance_id}: {e}")
        import traceback
        traceback.print_exc()
        return [], []
    finally:
        # Cleanup
        cleanup_container(client, container, instance_logger)
        close_logger(instance_logger)


def get_instances_to_process(
    dataset: List[dict],
    output_path: str,
    instance_ids: Optional[List[str]] = None,
) -> List[dict]:
    """
    Filter dataset to only instances that need processing.
    Skip instances that already have FAIL_TO_PASS and PASS_TO_PASS in output file.
    
    Args:
        dataset: Full dataset
        output_path: Path to output file
        instance_ids: Optional list of specific instance IDs to process
        
    Returns:
        Filtered list of instances to process
    """
    # Filter by instance_ids if specified
    if instance_ids:
        dataset = [inst for inst in dataset if inst['instance_id'] in instance_ids]
        logger.info(f"Filtered to {len(dataset)} instances based on instance_ids")
    
    # Check for already-processed instances in output file
    completed_ids = set()
    if Path(output_path).exists():
        try:
            with open(output_path, 'r') as f:
                existing_results = json.load(f)
            
            for inst in existing_results:
                # Check if instance has both FAIL_TO_PASS and PASS_TO_PASS fields
                if 'FAIL_TO_PASS' in inst and 'PASS_TO_PASS' in inst:
                    completed_ids.add(inst['instance_id'])
            
            if completed_ids:
                logger.info(f"Found {len(completed_ids)} already-processed instances in {output_path}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load existing results from {output_path}: {e}")
    
    # Filter out completed instances
    if completed_ids:
        original_count = len(dataset)
        dataset = [inst for inst in dataset if inst['instance_id'] not in completed_ids]
        skipped = original_count - len(dataset)
        if skipped > 0:
            logger.info(f"Skipping {skipped} already-processed instances")
    
    return dataset


def main(
    dataset_path: str,
    output_path: str,
    instance_ids: Optional[List[str]] = None,
    force_rebuild: bool = False,
    max_workers: int = 4,
    timeout: int = 1800,
):
    """
    Main function to collect tests for all instances in a dataset.
    
    Args:
        dataset_path: Path to input dataset JSON file
        output_path: Path to output dataset JSON file
        instance_ids: Optional list of specific instance IDs to process
        force_rebuild: Whether to force rebuild Docker images
        max_workers: Maximum number of workers for building images
        timeout: Timeout for test execution in seconds
    """
    # Load dataset
    logger.info(f"Loading dataset from {dataset_path}")
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    logger.info(f"Loaded {len(dataset)} instances")
    
    # Filter to instances that need processing
    dataset = get_instances_to_process(dataset, output_path, instance_ids)
    
    if not dataset:
        logger.info("No instances to process.")
        return
    
    # Initialize Docker client
    logger.info("Initializing Docker client...")
    client = docker.from_env()
    
    # Build environment images for all instances
    logger.info("Building environment images...")
    build_env_images(
        client,
        dataset,
        force_rebuild,
        max_workers,
        namespace=None,
        instance_image_tag="latest",
        env_image_tag="latest",
    )
    
    # Generate run ID
    import time
    run_id = f"collect_tests_{int(time.time())}"
    logger.info(f"Run ID: {run_id}")
    
    # Load existing results if output file exists
    existing_results = {}
    if Path(output_path).exists():
        try:
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
            existing_results = {inst['instance_id']: inst for inst in existing_data}
            logger.info(f"Loaded {len(existing_results)} existing results from {output_path}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load existing results: {e}")
    
    # Prepare payloads for parallel execution
    payloads = []
    for instance in dataset:
        payloads.append(
            (
                instance,
                client,
                run_id,
                force_rebuild,
                timeout,
            )
        )
    
    # Process instances in parallel with progress tracking
    logger.info(f"Processing {len(dataset)} instances in parallel with {max_workers} workers...")
    results = {}  # instance_id -> (fail_to_pass, pass_to_pass)
    lock = threading.Lock()
    pbar = tqdm(total=len(payloads), desc="Collecting tests")
    
    def save_result_to_file(instance_id: str, fail_to_pass: List[str], pass_to_pass: List[str]):
        """
        Save a single instance result to the output file incrementally.
        This function must be called within a lock to ensure thread safety.
        """
        try:
            # Load current file content
            current_data = []
            if Path(output_path).exists():
                with open(output_path, 'r') as f:
                    current_data = json.load(f)
            
            # Create a map of existing instances
            instance_map = {inst['instance_id']: inst for inst in current_data}
            
            # Find the instance data from the original dataset or existing results
            if instance_id in instance_map:
                inst = instance_map[instance_id].copy()
            else:
                # Find in the current dataset being processed
                inst = next((i for i in dataset if i['instance_id'] == instance_id), None)
                if inst is None:
                    logger.warning(f"Could not find instance {instance_id} in dataset")
                    return
                inst = inst.copy()
            
            # Update with new test results
            inst['FAIL_TO_PASS'] = fail_to_pass
            inst['PASS_TO_PASS'] = pass_to_pass
            
            # Update or add to the map
            instance_map[instance_id] = inst
            
            # Convert back to list and sort by instance_id for consistency
            updated_data = sorted(instance_map.values(), key=lambda x: x['instance_id'])
            
            # Write back to file
            with open(output_path, 'w') as f:
                json.dump(updated_data, f, indent=2)
            
            logger.info(f"Saved results for {instance_id} to {output_path}")
        except Exception as e:
            logger.error(f"Error saving result for {instance_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def collect_with_progress(*args):
        instance = args[0]
        instance_id = instance['instance_id']
        try:
            fail_to_pass, pass_to_pass = collect_tests_for_instance(*args)
            with lock:
                results[instance_id] = (fail_to_pass, pass_to_pass)
                # Save result incrementally to file
                save_result_to_file(instance_id, fail_to_pass, pass_to_pass)
                pbar.update()
            return (instance_id, fail_to_pass, pass_to_pass, None)
        except Exception as e:
            logger.error(f"Error processing {instance_id}: {e}")
            import traceback
            traceback.print_exc()
            with lock:
                results[instance_id] = ([], [])
                # Save empty result incrementally to file
                save_result_to_file(instance_id, [], [])
                pbar.update()
            return (instance_id, [], [], str(e))
    
    run_threadpool(collect_with_progress, payloads, max_workers)
    pbar.close()
    logger.info("All instances processed.")
    
    # Merge results with existing data
    updated_dataset = []
    all_instance_ids = set(inst['instance_id'] for inst in dataset) | set(existing_results.keys())
    
    # Create a map of all instances
    instance_map = {inst['instance_id']: inst for inst in dataset}
    
    for instance_id in sorted(all_instance_ids):
        if instance_id in existing_results:
            inst = existing_results[instance_id].copy()
        elif instance_id in instance_map:
            inst = instance_map[instance_id].copy()
        else:
            continue
        
        # Update with new results if available
        if instance_id in results:
            fail_to_pass, pass_to_pass = results[instance_id]
            inst['FAIL_TO_PASS'] = fail_to_pass
            inst['PASS_TO_PASS'] = pass_to_pass
        
        updated_dataset.append(inst)
    
    # Save final results
    logger.info(f"Saving final results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(updated_dataset, f, indent=2)
    
    # Save final results
    logger.info(f"\n{'='*80}")
    logger.info(f"Completed processing all instances")
    logger.info(f"Final results saved to {output_path}")
    logger.info(f"{'='*80}")
    
    # Print summary
    total_fail_to_pass = sum(len(inst['FAIL_TO_PASS']) for inst in updated_dataset)
    total_pass_to_pass = sum(len(inst['PASS_TO_PASS']) for inst in updated_dataset)
    instances_with_tests = sum(1 for inst in updated_dataset 
                               if len(inst['FAIL_TO_PASS']) > 0 or len(inst['PASS_TO_PASS']) > 0)
    
    logger.info(f"\nSummary:")
    logger.info(f"  Total instances: {len(updated_dataset)}")
    logger.info(f"  Instances with tests: {instances_with_tests}")
    logger.info(f"  Total FAIL_TO_PASS tests: {total_fail_to_pass}")
    logger.info(f"  Total PASS_TO_PASS tests: {total_pass_to_pass}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect FAIL_TO_PASS and PASS_TO_PASS tests for SWE-bench instances using Docker containers"
    )
    parser.add_argument(
        "dataset_path",
        type=str,
        help="Path to input dataset JSON file"
    )
    parser.add_argument(
        "output_path",
        type=str,
        help="Path to output dataset JSON file with collected tests"
    )
    parser.add_argument(
        "--instance-ids",
        nargs="+",
        help="Optional list of specific instance IDs to process"
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuild of Docker images"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum number of workers for building images (default: 8)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout for test execution in seconds (default: 1800)"
    )
    
    args = parser.parse_args()
    main(
        args.dataset_path,
        args.output_path,
        args.instance_ids,
        args.force_rebuild,
        args.max_workers,
        args.timeout,
    )

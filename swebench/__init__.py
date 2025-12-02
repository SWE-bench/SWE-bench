"""
SWE-bench: A benchmark for evaluating language models on software engineering tasks.

This package uses lazy imports (via __getattr__) to support minimal installation
for the testing module while maintaining backwards compatibility.

Installation options:
    - pip install swebench          # Full install (default, all dependencies)
    - pip install --no-deps swebench  # Minimal install (testing module only)

The lazy loading mechanism ensures that:
    1. 'from swebench.testing import ...' works with --no-deps (stdlib only)
    2. 'from swebench import run_evaluation' works when dependencies are present
    3. Backwards compatibility is maintained for existing code

See swebench.testing module for lightweight container testing utilities.
"""

__version__ = "4.1.0"


def __getattr__(name):
    """
    Lazy import mechanism to avoid loading dependencies on module import.
    
    This allows swebench.testing to be used with 'pip install --no-deps swebench'
    since it only uses stdlib. Other submodules are imported on-demand when accessed.
    """
    # Collect module imports
    if name == "build_dataset":
        from swebench.collect.build_dataset import main as build_dataset
        return build_dataset
    elif name == "get_tasks_pipeline":
        from swebench.collect.get_tasks_pipeline import main as get_tasks_pipeline
        return get_tasks_pipeline
    elif name == "print_pulls":
        from swebench.collect.print_pulls import main as print_pulls
        return print_pulls
    
    # Harness constants
    elif name == "KEY_INSTANCE_ID":
        from swebench.harness.constants import KEY_INSTANCE_ID
        return KEY_INSTANCE_ID
    elif name == "KEY_MODEL":
        from swebench.harness.constants import KEY_MODEL
        return KEY_MODEL
    elif name == "KEY_PREDICTION":
        from swebench.harness.constants import KEY_PREDICTION
        return KEY_PREDICTION
    elif name == "MAP_REPO_VERSION_TO_SPECS":
        from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS
        return MAP_REPO_VERSION_TO_SPECS
    
    # Docker build functions
    elif name == "build_image":
        from swebench.harness.docker_build import build_image
        return build_image
    elif name == "build_base_images":
        from swebench.harness.docker_build import build_base_images
        return build_base_images
    elif name == "build_env_images":
        from swebench.harness.docker_build import build_env_images
        return build_env_images
    elif name == "build_instance_images":
        from swebench.harness.docker_build import build_instance_images
        return build_instance_images
    elif name == "build_instance_image":
        from swebench.harness.docker_build import build_instance_image
        return build_instance_image
    elif name == "close_logger":
        from swebench.harness.docker_build import close_logger
        return close_logger
    elif name == "setup_logger":
        from swebench.harness.docker_build import setup_logger
        return setup_logger
    
    # Docker utils
    elif name == "cleanup_container":
        from swebench.harness.docker_utils import cleanup_container
        return cleanup_container
    elif name == "remove_image":
        from swebench.harness.docker_utils import remove_image
        return remove_image
    elif name == "copy_to_container":
        from swebench.harness.docker_utils import copy_to_container
        return copy_to_container
    elif name == "exec_run_with_timeout":
        from swebench.harness.docker_utils import exec_run_with_timeout
        return exec_run_with_timeout
    elif name == "list_images":
        from swebench.harness.docker_utils import list_images
        return list_images
    
    # Grading functions
    elif name == "compute_fail_to_pass":
        from swebench.harness.grading import compute_fail_to_pass
        return compute_fail_to_pass
    elif name == "compute_pass_to_pass":
        from swebench.harness.grading import compute_pass_to_pass
        return compute_pass_to_pass
    elif name == "get_logs_eval":
        from swebench.harness.grading import get_logs_eval
        return get_logs_eval
    elif name == "get_eval_report":
        from swebench.harness.grading import get_eval_report
        return get_eval_report
    elif name == "get_resolution_status":
        from swebench.harness.grading import get_resolution_status
        return get_resolution_status
    elif name == "ResolvedStatus":
        from swebench.harness.grading import ResolvedStatus
        return ResolvedStatus
    elif name == "TestStatus":
        from swebench.harness.grading import TestStatus
        return TestStatus
    
    # Log parsers
    elif name == "MAP_REPO_TO_PARSER":
        from swebench.harness.log_parsers import MAP_REPO_TO_PARSER
        return MAP_REPO_TO_PARSER
    
    # Run evaluation
    elif name == "run_evaluation":
        from swebench.harness.run_evaluation import main as run_evaluation
        return run_evaluation
    
    # Harness utils
    elif name == "run_threadpool":
        from swebench.harness.utils import run_threadpool
        return run_threadpool
    
    # Versioning constants
    elif name == "MAP_REPO_TO_VERSION_PATHS":
        from swebench.versioning.constants import MAP_REPO_TO_VERSION_PATHS
        return MAP_REPO_TO_VERSION_PATHS
    elif name == "MAP_REPO_TO_VERSION_PATTERNS":
        from swebench.versioning.constants import MAP_REPO_TO_VERSION_PATTERNS
        return MAP_REPO_TO_VERSION_PATTERNS
    
    # Versioning functions
    elif name == "get_version":
        from swebench.versioning.get_versions import get_version
        return get_version
    elif name == "get_versions_from_build":
        from swebench.versioning.get_versions import get_versions_from_build
        return get_versions_from_build
    elif name == "get_versions_from_web":
        from swebench.versioning.get_versions import get_versions_from_web
        return get_versions_from_web
    elif name == "map_version_to_task_instances":
        from swebench.versioning.get_versions import map_version_to_task_instances
        return map_version_to_task_instances
    elif name == "split_instances":
        from swebench.versioning.utils import split_instances
        return split_instances
    
    raise AttributeError(f"module 'swebench' has no attribute '{name}'")

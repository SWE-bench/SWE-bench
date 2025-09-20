__version__ = "4.0.4"

from swebench.collect.build_dataset import main as build_dataset
from swebench.collect.get_tasks_pipeline import main as get_tasks_pipeline
from swebench.collect.print_pulls import main as print_pulls

from swebench.types import (
    SWEbenchInstance,
)

from swebench.image_builder import (
    build_instance_images,
    build_instance_image,
)

from swebench.harness.docker_utils import (
    cleanup_container,
    copy_to_container,
    exec_run_with_timeout,
)

from swebench.harness.grading import (
    compute_fail_to_pass,
    compute_pass_to_pass,
    get_eval_report,
    get_resolution_status,
    ResolvedStatus,
    TestStatus,
)

from swebench.harness.log_parsers import (
    MAP_REPO_TO_PARSER,
)

from swebench.harness.run_evaluation import (
    main as run_evaluation,
)

from swebench.harness.utils import (
    run_threadpool,
)

from swebench.versioning.constants import (
    MAP_REPO_TO_VERSION_PATHS,
    MAP_REPO_TO_VERSION_PATTERNS,
)

from swebench.versioning.get_versions import (
    get_version,
    get_versions_from_build,
    get_versions_from_web,
    map_version_to_task_instances,
)

from swebench.versioning.utils import (
    split_instances,
)

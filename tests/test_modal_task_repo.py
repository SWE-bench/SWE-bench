"""Modal cannot run against a task repo, and says so.

Modal builds images remotely from the spec, so a run that passed --task-repo would
take its tests and patches from the tree while running code built from somewhere
else -- reporting on a tree it never actually built.
"""

import pytest

from swebench.harness.run_evaluation import main as run_evaluation


def test_modal_with_a_task_repo_is_refused(tmp_path):
    with pytest.raises(ValueError, match="cannot build from a task repo"):
        run_evaluation(
            dataset_name="SWE-bench/SWE-bench_Lite",
            split="test",
            instance_ids=["a__a-1"],
            predictions_path="gold",
            max_workers=1,
            open_file_limit=4096,
            run_id="modal-guard",
            timeout=1800,
            rewrite_reports=False,
            modal=True,
            task_repo="/nonexistent/tree",
        )

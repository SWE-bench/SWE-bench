"""Publish a run's results to a HuggingFace bucket + eval-results entry.

Uploads the files a run produced into a bucket, then writes one
``.eval_results/*.yaml`` entry scored against the report, in the Hub's community
eval-results format: https://huggingface.co/docs/hub/eval-results

This is a separate destination from the SWE-bench leaderboard flow in this package --
nothing here touches `experiments`, `metadata.yaml`, or swebench.com.
"""

import json
from pathlib import Path
from typing import Any, Optional, Union

import yaml

DEFAULT_ENDPOINT = "https://huggingface.co"

# The Hub serves a bucket's files at <bucket url>/resolve/<path in bucket>. The bucket
# URL itself is read back from create_bucket rather than assembled, so this segment is
# the only part of the file URL assumed here.
_FILE_SEGMENT = "resolve"


def upload_run(
    bucket_id: str,
    run_id: str,
    files: list[Union[str, Path]],
    *,
    private: bool = True,
    dry_run: bool = False,
    endpoint: Optional[str] = None,
) -> dict[str, Any]:
    """Upload ``files`` into ``bucket_id`` under a ``<run_id>/`` prefix.

    Returns a plan: the bucket, the paths written inside it (in the order given), and
    the base URL those paths are served from. With ``dry_run`` nothing is created and
    the base URL is predicted from the endpoint instead of read back from the Hub.
    """
    paths = [Path(f) for f in files]

    if missing := [str(p) for p in paths if not p.is_file()]:
        raise FileNotFoundError(
            f"cannot upload, file(s) not found: {', '.join(missing)}"
        )

    remote = [f"{run_id}/{p.name}" for p in paths]
    # Two local files with the same basename would land on the same bucket path and
    # silently overwrite each other, leaving the plan describing something untrue.
    if len(set(remote)) != len(remote):
        raise ValueError(
            f"duplicate file names would collide in the bucket: {sorted(remote)}"
        )

    plan: dict[str, Any] = {"bucket": bucket_id, "files": remote}

    if dry_run:
        plan["base_url"] = (
            f"{(endpoint or DEFAULT_ENDPOINT).rstrip('/')}/buckets/{bucket_id}"
        )
        return plan

    from huggingface_hub import HfApi

    api = HfApi(endpoint=endpoint) if endpoint else HfApi()
    bucket_url = api.create_bucket(bucket_id, private=private, exist_ok=True)
    api.batch_bucket_files(bucket_id, add=list(zip(paths, remote)))
    # create_bucket knows the real endpoint and namespace; deriving the base URL from it
    # keeps this working against a non-default endpoint (e.g. a private Hub deployment).
    plan["base_url"] = bucket_url.url.rstrip("/")
    return plan


def file_url(plan: dict[str, Any], remote_path: str) -> str:
    """Public URL of one uploaded file, given the plan ``upload_run`` returned."""
    if remote_path not in plan["files"]:
        raise ValueError(f"{remote_path!r} is not in this plan: {plan['files']}")
    return f"{plan['base_url']}/{_FILE_SEGMENT}/{remote_path}"


def resolved_percent(report: dict[str, Any]) -> float:
    """Percent of instances resolved, from a run report written by the harness."""
    total = report.get("total_instances") or 0
    if not total:
        raise ValueError(
            "report has no total_instances, so there is nothing to score -- is this a "
            "run report written by `swebench eval`?"
        )
    return 100.0 * report.get("resolved_instances", 0) / total


def read_report(report_path: Union[str, Path]) -> dict[str, Any]:
    return json.loads(Path(report_path).read_text())


def write_eval_result(
    dataset: str,
    task_id: str,
    value: float,
    source_url: str,
    out_path: Union[str, Path],
) -> Path:
    """Write one eval-results entry to ``out_path``, creating parent dirs."""
    entry = {
        "dataset": {"id": dataset, "task_id": task_id},
        "value": value,
        "source": {"url": source_url},
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump([entry], sort_keys=False))
    return out_path

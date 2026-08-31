"""Turn a finished evaluation run into a leaderboard submission.

A submission is two trees, because the heavy artifacts and the leaderboard entry live
in different places:

    submission-repo/        the submitter's own public GitHub repo
      all_preds.jsonl
      logs/<iid>/{patch.diff,report.json,test_output.txt[.gz]}
      trajs/<iid>.*
    entry/                  the PR to github.com/SWE-bench/experiments
      metadata.yaml
      README.md
      results/{results.json,resolved_by_repo.json,resolved_by_time.json}
      per_instance_details.json    (multilingual)

``logs/`` mirrors what the S3 bucket has always held, so existing consumers
(``analysis/download_logs.py``, the site's log links) keep working against a repo.

Resolution is **re-derived** here, never read from the run's own ``report.json``: each
instance is re-graded from its ``test_output.txt`` against the dataset, the same way
``experiments/analysis/get_results.py`` has always done it. A submission that ships a
doctored report still scores from its logs.
"""

import gzip
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from swebench.harness.constants import (
    LOG_REPORT,
    LOG_TEST_OUTPUT,
    RUN_EVALUATION_LOG_DIR,
)

# Directory name under experiments/evaluation/ -> the dataset it is scored against.
# `bash-only` is deliberately absent: those submissions now live under `verified`, with
# the harness identified by metadata tags rather than by a separate directory.
SPLIT_DATASETS = {
    "lite": "SWE-bench/SWE-bench_Lite",
    "verified": "SWE-bench/SWE-bench_Verified",
    "test": "SWE-bench/SWE-bench",
    "multilingual": "SWE-bench/SWE-bench_Multilingual",
    "multimodal": "SWE-bench/SWE-bench_Multimodal",
}

# Multimodal is evaluated through sb-cli, which produces no local logs or trajectories,
# so there is nothing for a submission repo to hold -- only the entry is built.
ENTRY_ONLY_SPLITS = {"multimodal"}

# GitHub warns above 50MB per file and rejects above 100MB. Test output is the only
# artifact that gets anywhere near it (verbose JS runners produce tens of MB), so it is
# gzipped, and anything still over this after compression is refused rather than left
# for `git push` to reject.
MAX_ARTIFACT_BYTES = 50 * 1024 * 1024


@dataclass
class PackageResult:
    split: str
    submission_id: str
    out_dir: Path
    resolved: list[str] = field(default_factory=list)
    no_generation: list[str] = field(default_factory=list)
    no_logs: list[str] = field(default_factory=list)
    oversized: list[str] = field(default_factory=list)

    @property
    def n_scored(self) -> int:
        return len(self.resolved)


class PackageError(RuntimeError):
    pass


def submission_id(model_name: str, when: Optional[datetime] = None) -> str:
    """``20260901_myagent`` -- the folder name experiments expects."""
    stamp = (when or datetime.now()).strftime("%Y%m%d")
    slug = model_name.replace("/", "__").replace(" ", "-")
    return f"{stamp}_{slug}"


def run_log_dir(run_id: str, model: str) -> Path:
    """Where `swebench eval` put this run's per-instance artifacts."""
    return RUN_EVALUATION_LOG_DIR / run_id / model.replace("/", "__")


def discover_model(run_id: str) -> str:
    """The single model directory inside a run, or an error naming the candidates."""
    root = RUN_EVALUATION_LOG_DIR / run_id
    if not root.is_dir():
        raise PackageError(f"no such run: {root} (is the run id right?)")
    models = sorted(d.name for d in root.iterdir() if d.is_dir())
    if not models:
        raise PackageError(f"run {run_id!r} has no model directories under {root}")
    if len(models) > 1:
        raise PackageError(
            f"run {run_id!r} holds several models ({', '.join(models)}); pass --model to pick one"
        )
    return models[0]


def load_predictions(path: Path) -> dict[str, dict]:
    """Read a .json or .jsonl predictions file into {instance_id: prediction}."""
    text = path.read_text()
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        loaded = json.loads(text)
        rows = list(loaded.values()) if isinstance(loaded, dict) else loaded
    return {r["instance_id"]: r for r in rows}


def _copy_artifact(src: Path, dest_dir: Path, oversized: list[str], iid: str) -> None:
    """Copy one artifact, gzipping test output and refusing what is still too large."""
    if src.name == LOG_TEST_OUTPUT:
        dest = dest_dir / f"{LOG_TEST_OUTPUT}.gz"
        with src.open("rb") as fin, gzip.open(dest, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        if dest.stat().st_size > MAX_ARTIFACT_BYTES:
            size_mb = dest.stat().st_size / 1024 / 1024
            dest.unlink()
            oversized.append(f"{iid} ({size_mb:.0f}MB gzipped)")
        return
    shutil.copy2(src, dest_dir / src.name)


def _grade(
    instance: dict, patch_path: Path, test_output_path: Path, model: str
) -> bool:
    """Re-derive one instance's verdict from its own test output.

    Deliberately ignores the run's report.json -- the log is the evidence, and grading
    it here is what lets anyone re-check a submission without trusting the submitter.
    """
    from swebench.harness.grading import get_eval_report
    from swebench.harness.utils import make_test_spec

    prediction = {
        "instance_id": instance["instance_id"],
        "model_patch": patch_path.read_text(),
        "model_name_or_path": model,
    }
    report = get_eval_report(
        make_test_spec(instance),
        prediction=prediction,
        test_log_path=str(test_output_path),
        include_tests_status=False,
    )
    return bool(report[instance["instance_id"]]["resolved"])


def _year(instance: dict) -> Optional[int]:
    created = instance.get("created_at")
    if not created:
        return None
    try:
        return datetime.fromisoformat(str(created).rstrip("Z")).year
    except ValueError:
        return None


def package_run(
    run_id: str,
    split: str,
    out_dir: Path,
    *,
    model: Optional[str] = None,
    predictions: Optional[Path] = None,
    trajs: Optional[Path] = None,
    sub_id: Optional[str] = None,
) -> PackageResult:
    """Build the submission-repo/ and entry/ trees for one evaluated run."""
    if split not in SPLIT_DATASETS:
        raise PackageError(
            f"unknown split {split!r}; expected one of {', '.join(sorted(SPLIT_DATASETS))}"
        )

    model = model or discover_model(run_id)
    logs_root = run_log_dir(run_id, model)
    if not logs_root.is_dir():
        raise PackageError(
            f"no logs for model {model!r} in run {run_id!r} ({logs_root})"
        )

    from datasets import load_dataset

    instances = {
        i["instance_id"]: i for i in load_dataset(SPLIT_DATASETS[split], split="test")
    }

    preds = load_predictions(predictions) if predictions else {}
    result = PackageResult(
        split=split, submission_id=sub_id or submission_id(model), out_dir=Path(out_dir)
    )
    entry = result.out_dir / "entry"
    (entry / "results").mkdir(parents=True, exist_ok=True)
    repo_dir = result.out_dir / "submission-repo"
    entry_only = split in ENTRY_ONLY_SPLITS
    if not entry_only:
        (repo_dir / "logs").mkdir(parents=True, exist_ok=True)

    by_repo: dict[str, dict[str, int]] = {}
    by_year: dict[int, dict[str, int]] = {}

    for iid, instance in sorted(instances.items()):
        bucket_repo = by_repo.setdefault(
            instance.get("repo", "?"), {"resolved": 0, "total": 0}
        )
        bucket_repo["total"] += 1
        if (year := _year(instance)) is not None:
            bucket_year = by_year.setdefault(year, {"resolved": 0, "total": 0})
            bucket_year["total"] += 1

        inst_logs = logs_root / iid
        patch_path, output_path = inst_logs / "patch.diff", inst_logs / LOG_TEST_OUTPUT
        if not inst_logs.is_dir() or not patch_path.is_file():
            result.no_generation.append(iid)
            continue
        if not output_path.is_file():
            result.no_logs.append(iid)
            continue

        if _grade(instance, patch_path, output_path, model):
            result.resolved.append(iid)
            bucket_repo["resolved"] += 1
            if year is not None:
                by_year[year]["resolved"] += 1

        if entry_only:
            continue
        dest = repo_dir / "logs" / iid
        dest.mkdir(parents=True, exist_ok=True)
        for artifact in (patch_path, inst_logs / LOG_REPORT, output_path):
            if artifact.is_file():
                _copy_artifact(artifact, dest, result.oversized, iid)

    if result.oversized:
        raise PackageError(
            "these instances' test output is too large to host in a git repo even "
            f"gzipped (>{MAX_ARTIFACT_BYTES // 1024 // 1024}MB): "
            + ", ".join(result.oversized)
        )

    (entry / "results" / "results.json").write_text(
        json.dumps(
            {
                "no_generation": sorted(result.no_generation),
                "no_logs": sorted(result.no_logs),
                "resolved": sorted(result.resolved),
            },
            indent=4,
        )
    )
    (entry / "results" / "resolved_by_repo.json").write_text(
        json.dumps(dict(sorted(by_repo.items())), indent=4)
    )
    (entry / "results" / "resolved_by_time.json").write_text(
        json.dumps({str(k): v for k, v in sorted(by_year.items())}, indent=4)
    )
    (entry / "metadata.yaml").write_text(_metadata_stub(result, model))
    (entry / "README.md").write_text(_readme_stub(result, model, len(instances)))

    if not entry_only:
        _write_predictions(repo_dir, preds, logs_root, model, instances)
        if trajs:
            _copy_trajs(Path(trajs), repo_dir / "trajs")

    return result


def _write_predictions(
    repo_dir: Path, preds: dict[str, dict], logs_root: Path, model: str, instances: dict
) -> None:
    """Write all_preds.jsonl -- from the predictions file if given, else rebuilt from
    each instance's patch.diff so a submission repo always carries its predictions."""
    rows = []
    for iid in sorted(instances):
        if iid in preds:
            rows.append(preds[iid])
            continue
        patch = logs_root / iid / "patch.diff"
        if patch.is_file():
            rows.append(
                {
                    "instance_id": iid,
                    "model_name_or_path": model,
                    "model_patch": patch.read_text(),
                }
            )
    (repo_dir / "all_preds.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows)
    )


def _copy_trajs(src: Path, dest: Path) -> None:
    """Copy reasoning traces, flattening mini-swe-agent's <iid>/<iid>.traj.json layout
    so every trace sits at trajs/<iid>.<ext>, as the leaderboard expects."""
    if not src.is_dir():
        raise PackageError(f"--trajs {src} is not a directory")
    dest.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        # <iid>/<iid>.traj.json -> <iid>.traj.json; a flat file keeps its own name
        name = (
            path.name
            if path.parent == src
            else f"{path.parent.name}{''.join(path.suffixes)}"
        )
        shutil.copy2(path, dest / name)


def _metadata_stub(result: PackageResult, model: str) -> str:
    """metadata.yaml with everything derivable filled in and the rest left as TODO.

    `assets` is written by `publish`, once the submission repo has a URL.
    """
    meta = {
        "info": {
            "name": "TODO leaderboard entry name",
            "site": "TODO url describing the system",
            "report": "TODO arXiv / technical report / blog post",
            "authors": "TODO",
            "logo": "TODO url, and commit the image as logo.png in this folder",
        },
        "tags": {
            "checked": False,
            "model": [model],
            "org": "TODO",
            "os_model": False,
            "os_system": False,
            "system": {"attempts": 1},
            "agent": "TODO harness name, without a version",
            "agent_org": "TODO who publishes the agent",
            "model_display": "TODO model as you want it written, no date suffix",
            "model_org": "TODO who publishes the model",
        },
    }
    header = (
        f"# Generated by `swebench submit package` for {result.submission_id}\n"
        f"# Scored {len(result.resolved)} resolved on the {result.split} split.\n"
        "# Replace every TODO before opening the PR; see experiments/checklist.md.\n"
        "# `assets` is added by `swebench submit publish`.\n"
    )
    return header + yaml.safe_dump(meta, sort_keys=False)


def _readme_stub(result: PackageResult, model: str, n_total: int) -> str:
    pct = 100.0 * len(result.resolved) / n_total if n_total else 0.0
    return f"""# {result.submission_id}

TODO: describe the system, and link the technical report.

| | |
| --- | --- |
| Split | `{result.split}` |
| Model | `{model}` |
| Resolved | {len(result.resolved)} / {n_total} ({pct:.2f}%) |
| No generation | {len(result.no_generation)} |
| Missing logs | {len(result.no_logs)} |

Resolution was re-derived from each instance's `test_output.txt` by
`swebench submit package`, not taken from the run's own report.
"""

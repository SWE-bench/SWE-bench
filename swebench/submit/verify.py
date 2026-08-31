"""Re-check a submission against its own artifacts.

This is what self-hosting buys: the logs a submission claims to be scored from are in a
public repo, so anyone can re-derive the verdicts and compare them to the entry's
``results.json``. Previously the artifacts lived in a maintainer-owned S3 bucket, so
only a maintainer could do this.

No Docker and no re-execution: the recorded test output is the evidence, and grading it
is deterministic.
"""

import gzip
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from swebench.harness.constants import LOG_TEST_OUTPUT
from swebench.submit.package import SPLIT_DATASETS, PackageError


class VerifyError(RuntimeError):
    pass


@dataclass
class VerifyResult:
    submission_id: str
    split: str
    n_checked: int = 0
    false_positives: list[str] = field(default_factory=list)  # claimed, does not hold
    false_negatives: list[str] = field(default_factory=list)  # holds, not claimed
    unbacked_claims: list[str] = field(default_factory=list)  # claimed, no log to check
    ungraded: list[str] = field(default_factory=list)  # no log, and not claimed either

    @property
    def ok(self) -> bool:
        """An unbacked claim counts as a failure.

        Shipping no log for an instance you claim to have resolved is the cheapest way
        to inflate a score, so it cannot pass. A missing log for an instance that is
        *not* claimed is only incomplete data, and does not fail the check.
        """
        return not (
            self.false_positives or self.false_negatives or self.unbacked_claims
        )


def _read_test_output(inst_dir: Path, dest: Path) -> Optional[Path]:
    """Materialize an instance's test output, transparently gunzipping it."""
    plain, gz = inst_dir / LOG_TEST_OUTPUT, inst_dir / f"{LOG_TEST_OUTPUT}.gz"
    if plain.is_file():
        return plain
    if gz.is_file():
        with gzip.open(gz, "rb") as fin, dest.open("wb") as fout:
            shutil.copyfileobj(fin, fout)
        return dest
    return None


def clone(repo_url: str, dest: Path) -> Path:
    """Shallow-clone a submission repo."""
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(dest)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise VerifyError(f"could not clone {repo_url}: {proc.stderr.strip()}")
    return dest


def resolve_artifacts(entry_dir: Path, logs_dir: Optional[Path], tmp: Path) -> Path:
    """Where this submission's logs/ live: a local path, or a clone of its repo."""
    if logs_dir:
        if not logs_dir.is_dir():
            raise VerifyError(f"--logs {logs_dir} is not a directory")
        return logs_dir
    meta = yaml.safe_load((entry_dir / "metadata.yaml").read_text()) or {}
    repo_url = (meta.get("assets") or {}).get("repo")
    if not repo_url:
        raise VerifyError(
            f"{entry_dir}/metadata.yaml has no assets.repo, so there is nothing to "
            "verify against -- pass --logs <dir> to check a local tree instead"
        )
    return clone(repo_url, tmp / "submission-repo") / "logs"


def verify(
    entry_dir: Path,
    split: str,
    *,
    logs_dir: Optional[Path] = None,
    model: str = "submission",
) -> VerifyResult:
    """Re-derive every instance's verdict and compare it to the entry's results.json."""
    entry_dir = Path(entry_dir)
    if split not in SPLIT_DATASETS:
        raise VerifyError(
            f"unknown split {split!r}; expected one of {', '.join(sorted(SPLIT_DATASETS))}"
        )
    results_path = entry_dir / "results" / "results.json"
    if not results_path.is_file():
        raise VerifyError(f"no results/results.json in {entry_dir}")
    claimed = set(json.loads(results_path.read_text()).get("resolved", []))

    from datasets import load_dataset

    from swebench.submit.package import _grade

    instances = {
        i["instance_id"]: i for i in load_dataset(SPLIT_DATASETS[split], split="test")
    }
    result = VerifyResult(submission_id=entry_dir.resolve().name, split=split)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        logs = resolve_artifacts(entry_dir, logs_dir, tmp_path)
        if not logs.is_dir():
            raise VerifyError(f"no logs/ directory found at {logs}")

        for inst_dir in sorted(d for d in logs.iterdir() if d.is_dir()):
            iid = inst_dir.name
            if iid not in instances:
                continue
            patch = inst_dir / "patch.diff"
            output = _read_test_output(inst_dir, tmp_path / f"{iid}.txt")
            if not patch.is_file() or output is None:
                (result.unbacked_claims if iid in claimed else result.ungraded).append(
                    iid
                )
                continue
            result.n_checked += 1
            try:
                holds = _grade(instances[iid], patch, output, model)
            except (PackageError, KeyError, ValueError) as exc:
                raise VerifyError(f"{iid}: could not grade ({exc})") from exc
            if holds and iid not in claimed:
                result.false_negatives.append(iid)
            elif not holds and iid in claimed:
                result.false_positives.append(iid)

        # A claim with no artifact directory at all. Must be collected before the
        # temp clone is removed.
        present = {d.name for d in logs.iterdir() if d.is_dir()}
        result.unbacked_claims.extend(sorted(claimed - present))

    return result

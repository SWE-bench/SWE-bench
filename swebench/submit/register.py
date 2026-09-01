"""Open the leaderboard PR for a packaged, published submission.

The PR adds one small folder to SWE-bench/experiments:

    evaluation/<split>/<submission_id>/
      metadata.yaml   README.md   results/*.json   logo.*

The heavy artifacts are not in it -- ``metadata.yaml``'s ``assets`` block points at the
submitter's own repo, which `publish` filled in.
"""

import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import yaml

from swebench.submit._git import (
    GitError,
    gh,
    gh_login,
    git,
    has_gh,
    init_commit,
    slug,
)

REGISTRY_DEFAULT = "https://github.com/SWE-bench/experiments"

# Fields package leaves as TODO. An entry that still carries them is not ready to open.
_TODO = re.compile(r"\bTODO\b")


class RegisterError(RuntimeError):
    pass


@dataclass
class RegisterPlan:
    submission_id: str
    split: str
    registry: str
    branch: str
    files: list[str] = field(default_factory=list)
    title: str = ""
    body: str = ""


@dataclass
class RegisterResult:
    plan: RegisterPlan
    pr_url: Optional[str] = None
    next_steps: Optional[str] = None


def unfilled_todos(entry_dir: Path) -> list[str]:
    """Dotted metadata paths still left as TODO, so they can be named in one error."""
    meta = yaml.safe_load((entry_dir / "metadata.yaml").read_text()) or {}
    found: list[str] = []

    def walk(node, prefix=""):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{prefix}{key}.")
        elif isinstance(node, list):
            for item in node:
                walk(item, prefix)
        elif isinstance(node, str) and _TODO.search(node):
            found.append(prefix.rstrip("."))

    walk(meta)
    if _TODO.search((entry_dir / "README.md").read_text()):
        found.append("README.md")
    return found


def resolve_split(out_dir: Path, split: Optional[str] = None) -> str:
    """The leaderboard split for a submission, from what `package` recorded.

    Falls back to the run the submission was built from, so a hand-assembled
    submission beside a run directory still resolves.
    """
    if split:
        return split
    from swebench.submit.package import (
        SPLIT_DATASETS,
        read_submission_meta,
        split_from_run,
    )

    meta = read_submission_meta(out_dir)
    if meta.get("split") in SPLIT_DATASETS:
        return meta["split"]
    if run_dir := meta.get("run_dir"):
        if found := split_from_run(Path(run_dir)):
            return found
    # <run>/submission/ is the default layout, so the run dir is the parent
    if found := split_from_run(Path(out_dir).resolve().parent):
        return found
    raise RegisterError(
        f"cannot tell which split {Path(out_dir).resolve()} belongs to -- pass --split"
    )


def read_entry(entry_dir: Path) -> dict:
    path = entry_dir / "metadata.yaml"
    if not path.is_file():
        raise RegisterError(f"no metadata.yaml in {entry_dir} -- run `package` first")
    return yaml.safe_load(path.read_text()) or {}


def build_plan(
    entry_dir: Path, split: str, submission_id: str, registry: str
) -> RegisterPlan:
    meta = read_entry(entry_dir)
    assets = meta.get("assets") or {}
    files = sorted(
        str(p.relative_to(entry_dir)) for p in entry_dir.rglob("*") if p.is_file()
    )
    resolved = "?"
    results = entry_dir / "results" / "results.json"
    if results.is_file():
        import json

        resolved = str(len(json.loads(results.read_text()).get("resolved", [])))
    body = (
        f"Adds `evaluation/{split}/{submission_id}/`.\n\n"
        f"- Split: `{split}`\n"
        f"- Resolved: {resolved}\n"
        f"- Artifacts: {assets.get('repo', 'TODO -- run `swebench submit publish`')}\n\n"
        "Checklist (see `checklist.md`):\n"
        "- [ ] pass@1 (one prediction per instance)\n"
        "- [ ] does not use `PASS_TO_PASS` / `FAIL_TO_PASS` knowledge\n"
        "- [ ] does not use the `hints` field\n"
        "- [ ] no web browsing, or steps taken to prevent solution lookup\n"
    )
    return RegisterPlan(
        submission_id=submission_id,
        split=split,
        registry=registry,
        branch=f"submission/{split}/{submission_id}",
        files=files,
        title=f"Add submission: {submission_id} ({split})",
        body=body,
    )


def write_entry(plan: RegisterPlan, entry_dir: Path, registry_root: Path) -> Path:
    """Copy the entry into a checkout of the registry at its final path."""
    dest = registry_root / "evaluation" / plan.split / plan.submission_id
    if dest.exists():
        raise RegisterError(f"{dest.relative_to(registry_root)} already exists")
    shutil.copytree(entry_dir, dest)
    return dest


def register(
    entry_dir: Path,
    split: str,
    submission_id: str,
    *,
    registry: str = REGISTRY_DEFAULT,
    allow_todos: bool = False,
    on_step: Optional[Callable[[str], None]] = None,
) -> RegisterResult:
    """Fork the registry, commit the entry on a branch, and open the PR.

    Always through a fork: submitters are outside the org, and a fork works whether or
    not you happen to have write access.

    ``on_step`` receives a line per step; cloning the registry and pushing take long
    enough that silence looks like a hang.
    """
    say = on_step or (lambda _msg: None)
    entry_dir = Path(entry_dir)
    if not allow_todos and (todos := unfilled_todos(entry_dir)):
        raise RegisterError(
            "these fields are still TODO: " + ", ".join(todos) + ". Fill them in "
            "(or pass --allow-todos to open a draft anyway)."
        )

    plan = build_plan(entry_dir, split, submission_id, registry)
    if not has_gh():
        return RegisterResult(
            plan=plan,
            next_steps=(
                "`gh` is not installed. Fork "
                f"{registry} yourself, copy this entry to "
                f"evaluation/{split}/{submission_id}/, and open a PR titled:\n"
                f"    {plan.title}"
            ),
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "experiments"
        try:
            say(f"forking and cloning {slug(registry)}")
            gh(Path(tmp), "repo", "fork", slug(registry), "--clone", "--", str(root))
        except GitError as exc:
            raise RegisterError(
                f"could not obtain a clone of {registry}: {exc}"
            ) from exc

        say(f"branching {plan.branch}")
        git(root, "checkout", "-q", "-b", plan.branch)
        say(f"adding evaluation/{split}/{submission_id}/ ({len(plan.files)} files)")
        write_entry(plan, entry_dir, root)
        init_commit(root, plan.title)
        try:
            say("pushing")
            git(root, "push", "-q", "-u", "origin", plan.branch)
            # Owner-qualified so gh never has to resolve the head itself, which is
            # what fails non-interactively for a cross-repo PR.
            head = f"{gh_login()}:{plan.branch}"
            say(f"opening pull request against {slug(registry)}")
            pr_url = gh(
                root,
                "pr",
                "create",
                "--repo",
                slug(registry),
                "--head",
                head,
                "--title",
                plan.title,
                "--body",
                plan.body,
            )
        except GitError as exc:
            return RegisterResult(
                plan=plan,
                next_steps=(
                    f"entry committed on branch {plan.branch}, but opening the PR "
                    f"failed: {exc}"
                ),
            )

    return RegisterResult(plan=plan, pr_url=pr_url.splitlines()[-1] if pr_url else None)

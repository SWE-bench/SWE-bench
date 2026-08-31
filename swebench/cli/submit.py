"""`swebench submit` -- prepare and publish a run's results.

Two destinations, one namespace:

* the SWE-bench leaderboard: ``package`` -> ``publish`` -> ``register``, with
  ``verify`` to re-check a submission against its own artifacts
* HuggingFace's community eval-results system: ``hf``
"""

import json
from typing import Optional

import typer

from swebench.cli._datasets import alias_help, resolve_dataset

submit_app = typer.Typer(
    no_args_is_help=True,
    help="""Prepare and publish a run's results.

[yellow][not dim][bold]Examples:[/bold][/not dim][/yellow]

    swebench submit hf my-run -b me/swebench-runs --report gpt5.my-run.json -d verified
""",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@submit_app.command("package")
def package_command(
    run_id: str = typer.Argument(..., help="Run id of a finished `swebench eval`"),
    split: str = typer.Option(
        ...,
        "-s",
        "--split",
        help="Leaderboard split: lite | verified | test | multilingual | multimodal",
    ),
    out: str = typer.Option(
        "submission", "-o", "--out", help="Directory to build into"
    ),
    model: Optional[str] = typer.Option(
        None,
        "-m",
        "--model",
        help="Model dir inside the run (auto-detected if only one)",
    ),
    predictions: Optional[str] = typer.Option(
        None,
        "-p",
        "--predictions",
        help="Predictions .json/.jsonl; rebuilt from patches if omitted",
    ),
    trajs: Optional[str] = typer.Option(
        None, "--trajs", help="Directory of reasoning traces to include"
    ),
    submission_id: Optional[str] = typer.Option(
        None, "--id", help="Submission folder name (default: <date>_<model>)"
    ),
):
    """Build a leaderboard submission from an evaluated run.

    Writes two trees: `submission-repo/` for your own public GitHub repo (predictions,
    logs, trajectories) and `entry/` for the PR to SWE-bench/experiments. Resolution is
    re-derived from each instance's test output, never read from the run's report.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit package my-run -s verified

        swebench submit package my-run -s verified --trajs ./output -o ./sub
    """
    from pathlib import Path as _Path

    from swebench.submit.package import PackageError, package_run

    try:
        result = package_run(
            run_id,
            split,
            _Path(out),
            model=model,
            predictions=_Path(predictions) if predictions else None,
            trajs=_Path(trajs) if trajs else None,
            sub_id=submission_id,
        )
    except PackageError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(
        f"{result.submission_id}: {len(result.resolved)} resolved, "
        f"{len(result.no_generation)} without a patch, {len(result.no_logs)} without logs"
    )
    typer.echo(
        f"  {result.out_dir / 'submission-repo'}  -> push to your own public repo"
    )
    typer.echo(
        f"  {result.out_dir / 'entry'}            -> PR to SWE-bench/experiments"
    )
    typer.echo(
        "Next: fill in the TODOs in entry/metadata.yaml, then `swebench submit publish`."
    )


@submit_app.command("publish")
def publish_command(
    out: str = typer.Argument("submission", help="Directory `package` built"),
    owner: str = typer.Option(
        "", "--owner", help="GitHub org/user (default: your account)"
    ),
    repo: str = typer.Option(
        "", "--repo", help="Repository name (default: the submission id)"
    ),
    private: bool = typer.Option(
        False,
        "--private",
        help="Create it private -- the leaderboard's log links will not resolve",
    ),
    remote: str = typer.Option(
        "", "--remote", help="Push to this existing empty repo instead of creating one"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Say what would happen; touch no network"
    ),
):
    """Push your submission's artifacts to your own public GitHub repo.

    Commits `submission-repo/`, pushes it, then writes the resulting URL into
    `entry/metadata.yaml` under `assets` -- the field that used to hold an s3:// path.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit publish ./submission --dry-run

        swebench submit publish ./submission --owner my-org
    """
    from pathlib import Path as _Path

    from swebench.submit._git import has_gh
    from swebench.submit.publish import PublishError, plan_repo_name, publish

    out_dir = _Path(out)
    if dry_run:
        name = repo or plan_repo_name(out_dir)
        target = f"{owner}/{name}" if owner else name
        how = (
            f"push to existing remote {remote}"
            if remote
            else f"`gh repo create {target}` ({'private' if private else 'public'}) and push"
            if has_gh()
            else "commit locally only -- no gh and no --remote"
        )
        typer.echo(f"Would publish {out_dir / 'submission-repo'}:\n  {how}")
        typer.echo("Dry run -- nothing committed, created, or pushed.")
        return

    if private:
        typer.echo(
            "warning: a private repo makes the leaderboard's log and trajectory links "
            "unreachable for everyone else.",
            err=True,
        )
    try:
        result = publish(
            out_dir, owner=owner, repo=repo, private=private, remote=remote
        )
    except PublishError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc

    if result.repo_url:
        typer.echo(f"published -> {result.repo_url} ({result.commit[:8]})")
        typer.echo("entry/metadata.yaml updated with assets.")
        typer.echo("Next: fill in remaining TODOs, then `swebench submit register`.")
    else:
        typer.echo(result.next_steps)


@submit_app.command("register")
def register_command(
    out: str = typer.Argument("submission", help="Directory `package` built"),
    split: str = typer.Option(..., "-s", "--split", help="Leaderboard split"),
    submission_id: Optional[str] = typer.Option(
        None, "--id", help="Folder name in experiments"
    ),
    registry: str = typer.Option(
        "", "--registry", help="Registry repo (default: SWE-bench/experiments)"
    ),
    allow_todos: bool = typer.Option(
        False, "--allow-todos", help="Open the PR with TODOs still unfilled"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the plan; touch no network"
    ),
):
    """Open the leaderboard PR, adding your entry to SWE-bench/experiments.

    Adds `evaluation/<split>/<id>/` -- metadata, README and results only. The heavy
    artifacts stay in your own repo, which `publish` recorded in `assets`.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit register ./submission -s verified --dry-run

        swebench submit register ./submission -s verified
    """
    from pathlib import Path as _Path

    from swebench.submit.publish import plan_repo_name
    from swebench.submit.register import (
        REGISTRY_DEFAULT,
        RegisterError,
        build_plan,
        register,
        unfilled_todos,
    )

    out_dir = _Path(out)
    entry_dir = out_dir / "entry" if (out_dir / "entry").is_dir() else out_dir
    sub_id = submission_id or plan_repo_name(out_dir)
    target = registry or REGISTRY_DEFAULT

    try:
        if dry_run:
            plan = build_plan(entry_dir, split, sub_id, target)
            todos = unfilled_todos(entry_dir)
            typer.echo(f"Would open: {plan.title}")
            typer.echo(f"  registry: {plan.registry}\n  branch:   {plan.branch}")
            typer.echo(f"  adds:     evaluation/{split}/{sub_id}/")
            for name in plan.files:
                typer.echo(f"              {name}")
            if todos:
                typer.echo(f"  BLOCKED by unfilled TODOs: {', '.join(todos)}")
            typer.echo("\nDry run -- nothing forked, pushed, or opened.")
            return
        result = register(
            entry_dir, split, sub_id, registry=target, allow_todos=allow_todos
        )
    except RegisterError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc

    if result.pr_url:
        typer.echo(f"opened {result.pr_url}")
    else:
        typer.echo(result.next_steps)


@submit_app.command("verify")
def verify_command(
    entry: str = typer.Argument(..., help="A submission entry directory"),
    split: str = typer.Option(..., "-s", "--split", help="Leaderboard split"),
    logs: Optional[str] = typer.Option(
        None, "--logs", help="Local logs/ to check instead of cloning the entry's repo"
    ),
):
    """Re-derive a submission's results and compare them to what it claims.

    Clones the repo named in the entry's `assets.repo`, re-grades every instance from
    its recorded test output, and reports any instance whose verdict disagrees. No
    Docker and no re-execution -- the log is the evidence.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit verify evaluation/verified/20260901_myagent -s verified

        swebench submit verify ./submission/entry -s verified --logs ./submission/submission-repo/logs
    """
    from pathlib import Path as _Path

    from swebench.submit.verify import VerifyError, verify

    try:
        result = verify(_Path(entry), split, logs_dir=_Path(logs) if logs else None)
    except VerifyError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"{result.submission_id}: re-graded {result.n_checked} instance(s)")
    for iid in result.unbacked_claims:
        typer.echo(f"  claimed resolved, but ships no log:  {iid}")
    if result.ungraded:
        typer.echo(
            f"  {len(result.ungraded)} unclaimed instance(s) had no usable log (not a failure)"
        )
    for iid in result.false_positives:
        typer.echo(f"  claimed resolved, does not hold: {iid}")
    for iid in result.false_negatives:
        typer.echo(f"  resolves but is not claimed:     {iid}")
    if result.ok:
        typer.echo("PASS -- the entry matches its artifacts.")
    else:
        typer.echo("FAIL -- discrepancies above.")
        raise typer.Exit(1)


@submit_app.command("hf")
def hf_command(
    run_id: str = typer.Argument(
        ..., help="Run id, used as the prefix inside the bucket"
    ),
    bucket: str = typer.Option(
        ..., "-b", "--bucket", help="HuggingFace bucket, as 'namespace/name'"
    ),
    report: str = typer.Option(..., "--report", help="Path to the run's report .json"),
    dataset: str = typer.Option(
        ...,
        "-d",
        "--dataset",
        help=f"Dataset the run scored against. Aliases: {alias_help()}",
    ),
    task_id: str = typer.Option(
        "swe_bench_%_resolved", "--task-id", help="eval-results task id"
    ),
    predictions: Optional[str] = typer.Option(
        None, "-p", "--predictions", help="Also upload this predictions file"
    ),
    out: str = typer.Option(
        ".eval_results/result.yaml",
        "--out",
        help="Where to write the eval-results entry",
    ),
    public: bool = typer.Option(
        False,
        "--public",
        help="Create the bucket public. Without this it is private, and the URL written "
        "into the eval-results entry will not be readable by anyone else.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print what would be uploaded; touch no network"
    ),
):
    """Upload a run to a HuggingFace bucket and write an eval-results entry.

    The entry is scored from the report's own resolved/total counts and points at the
    uploaded report ([link=https://huggingface.co/docs/hub/eval-results]format[/link]).

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit hf my-run -b me/swebench-runs --report gpt5.my-run.json -d verified

        swebench submit hf my-run -b me/runs --report r.json -d verified --dry-run
    """
    from swebench.submit.hf import (
        file_url,
        read_report,
        resolved_percent,
        upload_run,
        write_eval_result,
    )

    # Read and score the report before touching the network, so a malformed report fails
    # before a bucket has been created.
    report_data = read_report(report)
    value = resolved_percent(report_data)

    files = [report] + ([predictions] if predictions else [])
    plan = upload_run(bucket, run_id, files, private=not public, dry_run=dry_run)
    typer.echo(json.dumps(plan, indent=2))

    if dry_run:
        typer.echo(
            f"dry run -- would write {out} scoring {value:.2f} against "
            f"{resolve_dataset(dataset)}"
        )
        return

    if not public:
        typer.echo(
            "warning: the bucket is private, so the URL in the eval-results entry is "
            "not publicly readable. Pass --public if this entry is meant to be shared.",
            err=True,
        )

    out_path = write_eval_result(
        resolve_dataset(dataset),
        task_id,
        value,
        file_url(plan, plan["files"][0]),
        out,
    )
    typer.echo(f"wrote {out_path} ({value:.2f})")

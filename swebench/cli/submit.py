"""`swebench submit` -- prepare and publish a run's results.

Two destinations, one namespace:

* the SWE-bench leaderboard: ``package`` -> ``publish`` -> ``register``, with
  ``verify`` to re-check a submission against its own artifacts
* HuggingFace's community eval-results system: ``hf``
"""

import json
from pathlib import Path
from typing import Optional

import typer

from swebench.cli._datasets import alias_help, resolve_dataset

submit_app = typer.Typer(
    no_args_is_help=True,
    help="""Prepare and publish a run's results.

[yellow][not dim][bold]Create a leaderboard submission:[/bold][/not dim][/yellow]

  [bold]1.[/bold] Generate predictions
    swebench infer verified -c model.yaml --run-id demo

  [bold]2.[/bold] Evaluate them
    swebench eval verified -p logs/inference/demo/preds.json --run-id demo

  [bold]3.[/bold] Build the submission
    swebench submit package logs/evaluation/demo --trajs logs/inference/demo

  [bold]4.[/bold] Fill in the entry's metadata.yaml and README.md, and add a logo

  [bold]5.[/bold] Push the artifacts to a public repo of your own
    swebench submit publish logs/evaluation/demo -r <owner>/<name>

  [bold]6.[/bold] Check it reproduces, the way a reviewer would
    swebench submit verify logs/evaluation/demo

  [bold]7.[/bold] Open the pull request
    swebench submit register logs/evaluation/demo

[not dim]Every step after the first takes the same run directory. To publish to a
HuggingFace bucket instead, use [bold]swebench submit hf[/bold].[/not dim]
""",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@submit_app.command("package")
def package_command(
    run_path: Path = typer.Argument(
        ...,
        metavar="RUN_PATH",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="A finished run's log directory, e.g. logs/evaluation/<run_id>",
    ),
    split: Optional[str] = typer.Option(
        None,
        "-s",
        "--split",
        help="Leaderboard split; taken from the run's recorded dataset if omitted",
    ),
    out: Optional[str] = typer.Option(
        None,
        "-o",
        "--out",
        help="Directory to build into (default: <run>/submission)",
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

    Writes two trees under `<run>/submission/`: `submission-repo/` for your own public
    GitHub repo (predictions, logs, trajectories) and `entry/` for the PR to
    SWE-bench/experiments. The split comes from the dataset the run recorded. Resolution
    is re-derived from each instance's test output, never read from the run's report.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit package logs/evaluation/my-run

        swebench submit package logs/evaluation/my-run --trajs ./output -o ./sub
    """
    from pathlib import Path as _Path

    from swebench.submit.package import PackageError, package_run

    try:
        result = package_run(
            run_path,
            split,
            _Path(out) if out else None,
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
        + (f", {result.n_trajs} trajectories" if trajs else "")
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
    out: Path = typer.Argument(
        ...,
        metavar="RUN_PATH",
        exists=True,
        file_okay=False,
        help="A run directory, e.g. logs/evaluation/<run_id>",
    ),
    owner: str = typer.Option(
        "", "--owner", help="GitHub org/user (default: your account)"
    ),
    repo: str = typer.Option(
        "", "-r", "--repo", help="Repository to create, as <owner>/<name> or <name>"
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

    Name the destination with `--repo <owner>/<name>` to create it, or `--remote <url>`
    to push to a repo you already made. Commits `submission-repo/`, pushes it, then
    writes the resulting URL into `entry/metadata.yaml` under `assets` -- the field that
    used to hold an s3:// path.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit publish logs/evaluation/my-run/submission -r my-org/my-run --dry-run

        swebench submit publish logs/evaluation/my-run/submission -r my-org/my-run
    """
    from swebench.submit._git import has_gh
    from swebench.submit.package import PackageError, resolve_submission_dir
    from swebench.submit.publish import PublishError, plan_repo_name, publish

    try:
        out_dir = resolve_submission_dir(out)
    except PackageError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    if dry_run:
        from swebench.submit._git import origin

        if existing := origin(out_dir / "submission-repo"):
            how = f"push to its existing remote {existing}"
        elif remote:
            how = f"push to existing remote {remote}"
        elif repo:
            target = f"{owner}/{repo}" if owner and "/" not in repo else repo
            how = (
                f"`gh repo create {target}` ({'private' if private else 'public'}) and push"
                if has_gh()
                else f"cannot create {target} -- `gh` is not installed"
            )
        else:
            how = (
                "nothing -- name a destination with --repo <owner>/<name> or "
                f"--remote <url>. Suggested name: {plan_repo_name(out_dir)}"
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
            out_dir,
            owner=owner,
            repo=repo,
            private=private,
            remote=remote,
            on_step=lambda msg: typer.echo(f"  {msg}"),
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
    out: Path = typer.Argument(
        ...,
        metavar="RUN_PATH",
        exists=True,
        file_okay=False,
        help="A run directory, e.g. logs/evaluation/<run_id>",
    ),
    split: Optional[str] = typer.Option(
        None,
        "-s",
        "--split",
        help="Leaderboard split; taken from the submission if omitted",
    ),
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
    artifacts stay in your own repo, which `publish` recorded in `assets`. The split and
    the submission id come from what `package` recorded.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit register logs/evaluation/my-run/submission --dry-run

        swebench submit register logs/evaluation/my-run/submission
    """
    from swebench.submit.package import (
        PackageError,
        resolve_entry_dir,
        resolve_submission_dir,
    )
    from swebench.submit.publish import plan_repo_name
    from swebench.submit.register import (
        REGISTRY_DEFAULT,
        RegisterError,
        build_plan,
        register,
        resolve_split,
        unfilled_todos,
    )

    try:
        out_dir = resolve_submission_dir(out)
        entry_dir = resolve_entry_dir(out)
    except PackageError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
    sub_id = submission_id or plan_repo_name(out_dir)
    target = registry or REGISTRY_DEFAULT

    try:
        split = resolve_split(out_dir, split)
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
            entry_dir,
            split,
            sub_id,
            registry=target,
            allow_todos=allow_todos,
            on_step=lambda msg: typer.echo(f"  {msg}"),
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
    entry: Path = typer.Argument(
        ...,
        metavar="RUN_PATH",
        exists=True,
        file_okay=False,
        help="A run directory, or an entry already committed to experiments",
    ),
    split: Optional[str] = typer.Option(
        None,
        "-s",
        "--split",
        help="Leaderboard split; inferred from the path if omitted",
    ),
    logs: Optional[str] = typer.Option(
        None, "--logs", help="Local logs/ to check instead of cloning the entry's repo"
    ),
):
    """Re-derive a submission's results and compare them to what it claims.

    Clones the repo named in the entry's `assets.repo`, re-grades every instance from
    its recorded test output, and reports any instance whose verdict disagrees. No
    Docker and no re-execution -- the log is the evidence.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit verify evaluation/verified/20260901_myagent

        swebench submit verify logs/evaluation/my-run/submission/entry
    """
    from pathlib import Path as _Path

    from swebench.submit.package import PackageError, resolve_entry_dir
    from swebench.submit.verify import VerifyError, verify

    try:
        result = verify(
            resolve_entry_dir(entry), split, logs_dir=_Path(logs) if logs else None
        )
    except PackageError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc
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
    run: str = typer.Argument(
        ..., metavar="RUN_PATH", help="A run directory, or a bare run id"
    ),
    bucket: str = typer.Option(
        ..., "-b", "--bucket", help="HuggingFace bucket, as 'namespace/name'"
    ),
    report: Optional[str] = typer.Option(
        None,
        "--report",
        help="Path to the run's results.json (default: the run's own log directory)",
    ),
    dataset: Optional[str] = typer.Option(
        None,
        "-d",
        "--dataset",
        help=f"Dataset the run scored against; taken from the run if omitted. "
        f"Aliases: {alias_help()}",
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

    The report and the dataset both come from the run itself, so only the bucket has to
    be named. The entry is scored from the report's resolved/total counts and points at
    the uploaded report
    ([link=https://huggingface.co/docs/hub/eval-results]format[/link]).

    [yellow][bold]Examples:[/bold][/yellow]

        swebench submit hf my-run -b me/swebench-runs

        swebench submit hf my-run -b me/runs --dry-run
    """
    from pathlib import Path as _Path

    from swebench.harness.constants import LOG_RUN_METADATA
    from swebench.submit.package import resolve_run
    from swebench.submit.hf import (
        file_url,
        read_report,
        resolved_percent,
        upload_run,
        write_eval_result,
    )

    run_id, run_dir = resolve_run(run)
    report_path = _Path(report) if report else run_dir / "results.json"
    if not report_path.is_file():
        typer.echo(
            f"error: no report at {report_path.resolve()}. Run `swebench eval` first, "
            "or pass --report.",
            err=True,
        )
        raise typer.Exit(1)

    if dataset is None:
        meta_path = run_dir / LOG_RUN_METADATA
        recorded = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
        if not recorded.get("dataset"):
            typer.echo(
                f"error: run {run_id!r} did not record which dataset it used, so pass -d.",
                err=True,
            )
            raise typer.Exit(1)
        dataset = recorded["dataset"]

    # Read and score the report before touching the network, so a malformed report fails
    # before a bucket has been created.
    value = resolved_percent(read_report(report_path))

    files = [str(report_path)] + ([predictions] if predictions else [])
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

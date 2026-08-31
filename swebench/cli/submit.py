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

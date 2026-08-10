"""`swebench eval` and `swebench report`."""

from typing import Optional

import typer

from swebench.cli._datasets import alias_help, resolve_dataset

DATASET_ARG = typer.Argument(
    ...,
    metavar="DATASET",
    help=f"Dataset alias, HuggingFace id, or local path. Aliases: {alias_help()}",
)


def eval_command(
    dataset: str = DATASET_ARG,
    gold: bool = typer.Option(False, "--gold", help="Evaluate the reference patches"),
    predictions: Optional[str] = typer.Option(
        None, "-p", "--predictions", help="Path to a predictions .json/.jsonl"
    ),
    run_id: str = typer.Option("run", "--run-id", help="Names the log directory"),
    instance_ids: Optional[list[str]] = typer.Option(
        None, "-i", "--instance", help="Limit to these instances (repeatable)"
    ),
    split: str = typer.Option("test", "-s", "--split"),
    workers: int = typer.Option(4, "-j", "--workers", help="Instances evaluated in parallel"),
    timeout: int = typer.Option(1800, "-t", "--timeout", help="Per-instance seconds"),
    report_dir: str = typer.Option(".", "--report-dir"),
    modal: bool = typer.Option(False, "--modal", help="Run on Modal instead of local Docker"),
    open_file_limit: int = typer.Option(4096, "--open-file-limit"),
):
    """Evaluate gold or model predictions against a dataset.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench eval verified --gold

        swebench eval lite -p preds.jsonl --run-id gpt5 -j 16

        swebench eval multimodal --gold -i carbon-design-system__carbon-10188

        swebench eval full --gold --modal
    """
    if gold and predictions:
        raise typer.BadParameter("pass either --gold or --predictions, not both")
    if not gold and not predictions:
        raise typer.BadParameter("pass --gold or --predictions <path>")

    from swebench.harness.run_evaluation import main as run_evaluation

    run_evaluation(
        dataset_name=resolve_dataset(dataset),
        split=split,
        instance_ids=list(instance_ids) if instance_ids else None,
        predictions_path="gold" if gold else predictions,
        max_workers=workers,
        open_file_limit=open_file_limit,
        run_id=run_id,
        timeout=timeout,
        rewrite_reports=False,
        modal=modal,
        report_dir=report_dir,
    )


def report_command(
    run_id: str = typer.Argument(..., help="Run id to re-grade"),
    dataset: str = typer.Option("verified", "-d", "--dataset", help="Dataset the run used"),
    split: str = typer.Option("test", "-s", "--split"),
    instance_ids: Optional[list[str]] = typer.Option(None, "-i", "--instance"),
    report_dir: str = typer.Option(".", "--report-dir"),
):
    """Re-grade a finished run from its saved logs, without starting containers.

    Useful after a log-parser fix: the test output is already on disk, so the
    verdicts can be recomputed in seconds.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench report my-run -d verified

        swebench report my-run -d multimodal -i grommet__grommet-6282
    """
    from swebench.harness.run_evaluation import main as run_evaluation

    run_evaluation(
        dataset_name=resolve_dataset(dataset),
        split=split,
        instance_ids=list(instance_ids) if instance_ids else None,
        predictions_path="gold",
        max_workers=1,
        open_file_limit=4096,
        run_id=run_id,
        timeout=1800,
        rewrite_reports=True,
        modal=False,
        report_dir=report_dir,
    )

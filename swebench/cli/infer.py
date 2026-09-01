"""`swebench infer` -- run mini-SWE-agent over a dataset to produce predictions."""

from pathlib import Path
from typing import Optional

import typer

from swebench.cli._datasets import alias_help, resolve_dataset
from swebench.harness.constants import INFERENCE_LOG_DIR


def infer_command(
    ctx: typer.Context,
    dataset: str = typer.Argument(
        ...,
        metavar="DATASET",
        help=f"Dataset alias, HuggingFace id, or local path. Aliases: {alias_help()}",
    ),
    model: Optional[str] = typer.Option(
        None, "-m", "--model", help="Model name, as litellm spells it"
    ),
    run_id: str = typer.Option("run", "--run-id", help="Names the output directory"),
    output: Optional[str] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output directory (default: logs/inference/<run_id>)",
    ),
    split: str = typer.Option("test", "-s", "--split"),
    workers: int = typer.Option(
        1, "-w", "--workers", help="Instances inferred in parallel"
    ),
    config: Optional[list[str]] = typer.Option(
        None,
        "-c",
        "--config",
        help="Extra mini-SWE-agent config file or key=value, after its bundled default "
        "(repeatable)",
    ),
    python: Optional[str] = typer.Option(
        None,
        "--python",
        help="Interpreter that has mini-SWE-agent installed, if not this one",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the command that would run and exit"
    ),
):
    """Generate predictions with mini-SWE-agent, writing preds.json + trajectories.

    A thin wrapper around `mini-extra swebench`: it resolves SWE-bench's dataset
    aliases and passes mini's bundled config explicitly (mini drops its own default the
    moment any -c is given). Unrecognized arguments go straight through to mini, so
    `--filter`, `--slice` and friends work as documented there.

    The model's API key is mini's business, not this command's -- export whatever the
    provider needs before running. Note that `api_key: os.environ/VAR` inside a model
    config is [bold]not[/bold] resolved by litellm outside its proxy, so set the real
    environment variable the provider reads instead.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench infer verified -m gpt-5 --run-id gpt5 -w 8

        swebench infer verified -c model.yaml -w 12 -o output

        swebench infer lite -m gpt-5 --dry-run -- --filter "astropy.*"

        swebench infer verified -c model.yaml --python /path/to/venv/bin/python
    """
    from swebench.inference.mini_swe_agent import (
        InferenceError,
        INSTALL_HINT,
        build_command,
        is_available,
        run,
    )

    if not is_available(python):
        typer.echo(INSTALL_HINT, err=True)
        raise typer.Exit(1)

    out_dir = Path(output) if output else INFERENCE_LOG_DIR / run_id
    try:
        cmd = build_command(
            resolve_dataset(dataset),
            output=out_dir,
            split=split,
            workers=workers,
            model=model,
            configs=tuple(config or ()),
            extra=tuple(ctx.args),
            python=python,
        )
    except InferenceError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(" ".join(cmd))
    if dry_run:
        return
    raise typer.Exit(run(cmd))

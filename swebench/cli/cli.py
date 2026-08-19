"""Main CLI entry point. Defines the top-level app and wires the sub-apps."""

import logging

import typer

_PANEL_EVAL = "Evaluate"
_PANEL_IMAGES = "Images"
_PANEL_DATA = "Datasets"

app = typer.Typer(
    name="swebench",
    help="""SWE-bench - evaluate language models on real GitHub issues.

[yellow][not dim][bold]Examples:[/bold][/not dim][/yellow]

    swebench eval verified --gold
    swebench eval verified -p preds.jsonl --run-id gpt5 -j 16
    swebench eval multimodal --gold -i carbon-design-system__carbon-10188
    swebench report my-run -d verified
    swebench publish gpt5 -b myuser/swebench-runs -p preds.jsonl --model-id openai/gpt-5
    swebench images build verified -j 8
    swebench images check multilingual
    swebench images clean --run-id my-run
    swebench dataset build multimodal -s test
    swebench dataset collect scikit-learn/scikit-learn
""",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def _global_options(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable DEBUG logging"),
) -> None:
    if verbose:
        logging.getLogger("swebench").setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)


def main():
    app()


from swebench.cli.dataset import dataset_app  # noqa: E402
from swebench.cli.evaluate import (  # noqa: E402
    eval_command,
    publish_command,
    report_command,
)
from swebench.cli.images import images_app  # noqa: E402

app.command("eval", rich_help_panel=_PANEL_EVAL)(eval_command)
app.command("report", rich_help_panel=_PANEL_EVAL)(report_command)
app.command("publish", rich_help_panel=_PANEL_EVAL)(publish_command)
app.add_typer(images_app, name="images", rich_help_panel=_PANEL_IMAGES)
app.add_typer(dataset_app, name="dataset", rich_help_panel=_PANEL_DATA)

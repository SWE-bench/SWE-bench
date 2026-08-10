"""`swebench dataset` — build, collect and version task instances."""

from typing import Optional

import typer

from swebench.cli._datasets import alias_help, resolve_dataset

dataset_app = typer.Typer(
    name="dataset",
    help="Build, collect and version task instances.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@dataset_app.command("build")
def build(
    dataset: str = typer.Argument(
        ..., metavar="DATASET", help=f"Dataset alias or HuggingFace id. Aliases: {alias_help()}"
    ),
    split: Optional[list[str]] = typer.Option(None, "-s", "--split", help="Splits to build (repeatable)"),
    out: Optional[str] = typer.Option(None, "-o", "--out", help="Output directory (default: ./data)"),
    dockerfile_repos: Optional[str] = typer.Option(
        None, "--dockerfile-repos", help="Directory holding the swe-bench-*-dockerfiles checkouts"
    ),
):
    """Regenerate a dataset's parquet, including the fields the harness reads.

    Joins the public columns from HuggingFace with the eval scripts, parsers and
    image names produced by the dockerfile repos' generators, writing
    eval_script, log_parser, eval_type and image alongside them. Run this after
    changing a generator, then push the result to HuggingFace.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench dataset build multimodal -s test

        swebench dataset build verified --dockerfile-repos ~/code

        swebench dataset build lite -s dev -s test -o /tmp/out
    """
    import os
    from pathlib import Path

    if dockerfile_repos:
        os.environ["SWEBENCH_DOCKERFILE_REPOS"] = dockerfile_repos
    if out:
        os.environ["SWEBENCH_DATA_DIR"] = out

    from swebench.collect import build_local_datasets as b

    full = resolve_dataset(dataset)
    short = full.split("/")[-1]
    configs = {
        "SWE-bench": (b.MAP_REPO_TO_PARSER_NAME_OG, b.FAIL_ONLY_REPOS_OG, "og", {"environment_setup_commit"}),
        "SWE-bench_Lite": (b.MAP_REPO_TO_PARSER_NAME_OG, b.FAIL_ONLY_REPOS_OG, "og", {"environment_setup_commit"}),
        "SWE-bench_Verified": (
            b.MAP_REPO_TO_PARSER_NAME_OG, b.FAIL_ONLY_REPOS_OG, "og",
            {"environment_setup_commit", "difficulty"},
        ),
        "SWE-bench_Multilingual": (
            b.MAP_REPO_TO_PARSER_NAME_MULTILINGUAL, b.FAIL_ONLY_REPOS_MULTILINGUAL, "multilingual", None,
        ),
        "SWE-bench_Multimodal": (
            b.MAP_REPO_TO_PARSER_NAME_MULTIMODAL, b.FAIL_ONLY_REPOS_MULTIMODAL, "multimodal", {"image_assets"},
        ),
    }
    if short not in configs:
        raise typer.BadParameter(f"no generator config for {full}; expected one of {list(configs)}")

    parser_map, fail_only, key, extra = configs[short]
    base = Path(os.environ.get("SWEBENCH_DATA_DIR", Path.cwd() / "data"))
    b.process_dataset(
        hf_name=full,
        parser_map=parser_map,
        fail_only_repos=fail_only,
        generator_key=key,
        output_dir=base / short,
        label=short,
        extra_required_fields=extra,
        splits=list(split) if split else None,
    )


@dataset_app.command("collect")
def collect(
    repos: list[str] = typer.Argument(..., help="GitHub repos, e.g. scikit-learn/scikit-learn"),
    path_prs: str = typer.Option("prs", "--path-prs", help="Where to write the scraped PRs"),
    path_tasks: str = typer.Option("tasks", "--path-tasks", help="Where to write candidate instances"),
    max_pulls: Optional[int] = typer.Option(None, "--max-pulls", help="Stop after this many PRs"),
    cutoff_date: Optional[str] = typer.Option(None, "--cutoff-date", help="Ignore PRs before YYYYMMDD"),
):
    """Scrape pull requests from GitHub into candidate task instances.

    Produces <repo>-prs.jsonl and <repo>-task-instances.jsonl. The candidates
    still need versions, install specs and validation before they are usable.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench dataset collect scikit-learn/scikit-learn

        swebench dataset collect psf/requests --max-pulls 200 --cutoff-date 20230101
    """
    from swebench.collect.get_tasks_pipeline import main as get_tasks

    get_tasks(
        repos=list(repos),
        path_prs=path_prs,
        path_tasks=path_tasks,
        max_pulls=max_pulls,
        cutoff_date=cutoff_date,
    )


@dataset_app.command("versions")
def versions(
    instances_path: str = typer.Argument(..., help="Task instances .jsonl from `dataset collect`"),
    retrieval_method: str = typer.Option(
        "github", "--retrieval-method", help="github, build, or mix"
    ),
    output_dir: str = typer.Option("versions", "--output-dir"),
    workers: int = typer.Option(4, "-j", "--workers"),
    testbed: Optional[str] = typer.Option(None, "--testbed", help="Scratch dir for build-based lookup"),
    conda_env: Optional[str] = typer.Option(None, "--conda-env"),
    path_conda: Optional[str] = typer.Option(None, "--path-conda"),
    cleanup: bool = typer.Option(False, "--cleanup"),
):
    """Attach a version to each task instance.

    Install specs are keyed by version, so instances without one cannot be built.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench dataset versions tasks/scikit-learn-task-instances.jsonl

        swebench dataset versions tasks/foo.jsonl --retrieval-method build --testbed /tmp/tb
    """
    from swebench.versioning.get_versions import main as get_versions

    get_versions(
        instances_path=instances_path,
        retrieval_method=retrieval_method,
        cleanup=cleanup,
        conda_env=conda_env,
        num_workers=workers,
        path_conda=path_conda,
        testbed=testbed,
        output_dir=output_dir,
    )

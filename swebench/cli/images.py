"""`swebench images` — build, check and clean instance images."""

from typing import Optional

import typer

from swebench.cli._datasets import alias_help, resolve_dataset

images_app = typer.Typer(
    name="images",
    help="Build, check and clean instance images.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

DATASET_ARG = typer.Argument(
    ..., metavar="DATASET", help=f"Dataset alias, HuggingFace id, or local path. Aliases: {alias_help()}"
)


@images_app.command("build")
def build(
    dataset: str = DATASET_ARG,
    split: str = typer.Option("test", "-s", "--split"),
    instance_ids: Optional[list[str]] = typer.Option(
        None, "-i", "--instance", help="Only these instances (repeatable)"
    ),
    workers: int = typer.Option(4, "-j", "--workers"),
    force_rebuild: bool = typer.Option(False, "--force-rebuild"),
    namespace: Optional[str] = typer.Option(None, "-n", "--namespace", help="Registry namespace to tag for"),
    tag: Optional[str] = typer.Option(None, "--tag"),
    dockerfile_repo: Optional[str] = typer.Option(None, "--dockerfile-repo", help="Path or GitHub ref"),
    dry_run: bool = typer.Option(False, "--dry-run", help="List what would be built"),
    open_file_limit: int = typer.Option(4096, "--open-file-limit"),
):
    """Build images ahead of an evaluation.

    Images are per instance but always selected through a dataset, since the
    Dockerfile comes from the instance row. Use -i to narrow to a subset.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench images build verified -j 8

        swebench images build multimodal -i carbon-design-system__carbon-10188

        swebench images build lite --dry-run
    """
    from swebench.image_builder.prepare_images import main as prepare_images

    prepare_images(
        dataset_name=resolve_dataset(dataset),
        split=split,
        instance_ids=list(instance_ids) if instance_ids else None,
        max_workers=workers,
        force_rebuild=force_rebuild,
        open_file_limit=open_file_limit,
        namespace=namespace,
        tag=tag,
        dry_run=dry_run,
        dockerfile_repo=dockerfile_repo,
    )


@images_app.command("check")
def check(
    dataset: str = DATASET_ARG,
    split: str = typer.Option("test", "-s", "--split"),
    workers: int = typer.Option(16, "-j", "--workers"),
):
    """Report which of a dataset's images are missing from the registry.

    Catches a stale or partially-pushed image set before an evaluation spends
    hours discovering it one instance at a time.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench images check verified

        swebench images check multilingual -j 32
    """
    from concurrent.futures import ThreadPoolExecutor

    import docker

    from swebench.harness.utils import load_swebench_dataset

    client = docker.from_env()
    instances = load_swebench_dataset(resolve_dataset(dataset), split)
    names = sorted({i["image"] for i in instances if i.get("image")})
    if not names:
        typer.echo("dataset rows carry no image field")
        raise typer.Exit(1)

    def present(name: str) -> tuple[str, bool]:
        try:
            client.images.get_registry_data(name)
            return name, True
        except Exception:
            return name, False

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(present, names))

    missing = [n for n, ok in results if not ok]
    typer.echo(f"{len(names) - len(missing)}/{len(names)} images present")
    for name in missing:
        typer.echo(f"  missing {name}")
    raise typer.Exit(1 if missing else 0)


@images_app.command("clean")
def clean(
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Remove containers from this run"),
    instance_ids: Optional[list[str]] = typer.Option(None, "-i", "--instance"),
    predictions: Optional[str] = typer.Option(None, "-p", "--predictions"),
):
    """Remove leftover evaluation containers.

    A killed run leaves containers holding their names, and the next attempt
    fails with a 409 conflict.

    [yellow][bold]Examples:[/bold][/yellow]

        swebench images clean --run-id my-run

        swebench images clean -i astropy__astropy-12907
    """
    from swebench.harness.remove_containers import main as remove_containers

    remove_containers(
        instance_ids=list(instance_ids) if instance_ids else None,
        predictions_path=predictions,
        run_id=run_id,
    )

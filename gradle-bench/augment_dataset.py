"""Extend a gradle-bench dataset with per-task ``test_cmd`` and ``image_name``.

Both values live only in the Python specs
(``swebench/harness/constants/kotlin_base.py``, overridden per-repo in
``swebench/harness/repo_customization/*.py``):

* ``test_cmd`` is ``MAP_REPO_VERSION_TO_SPECS[repo][version]["test_cmd"]`` (a
  list of shell commands).
* ``image_name`` is the eval image tag, resolved exactly as
  ``TestSpec.instance_image_key`` does: ``sweb.eval.{arch}.{instance_id}:{tag}``,
  where ``arch`` honours the per-repo ``docker_specs["arch"]`` override (e.g.
  Kotlin/Native repos pinned to x86_64), and a ``namespace`` prefix is added for
  remote images.

This script bakes both into the dataset so downstream consumers read them from
the data instead of re-mirroring the constants.

Usage:
  python augment_dataset.py DATASET.json [--output OUT.json] [--instance_ids ID ...]
                           [--arch ARCH] [--namespace NS] [--instance_image_tag TAG]

The dataset is rewritten in place unless ``--output`` is given. Re-running is
idempotent.
"""
import argparse
import json

from swebench.harness.constants import LATEST, MAP_REPO_VERSION_TO_SPECS
from swebench.harness.dockerfiles import get_host_arch


def _resolve_image_name(
    instance_id: str,
    specs: dict,
    arch: str,
    namespace: str | None,
    instance_image_tag: str,
) -> str:
    """Mirror ``TestSpec.instance_image_key`` for a single instance.

    Honours the per-repo ``docker_specs["arch"]`` override and the remote-image
    namespace prefix, so the baked value matches what the harness builds.
    """
    arch = specs.get("docker_specs", {}).get("arch") or arch
    key = f"sweb.eval.{arch}.{instance_id.lower()}:{instance_image_tag}"
    if namespace is not None:
        key = f"{namespace}/{key}".replace("__", "_1776_")
    return key


def augment_dataset(
    dataset: list,
    instance_ids: list | None = None,
    arch: str | None = None,
    namespace: str | None = None,
    instance_image_tag: str = LATEST,
) -> int:
    """Add ``test_cmd`` and ``image_name`` to each task, resolved from the specs.

    ``arch`` defaults to the host architecture (per-repo ``docker_specs["arch"]``
    overrides still take precedence). Returns the number of tasks augmented.
    Raises ValueError listing any (repo, version) pairs missing from
    MAP_REPO_VERSION_TO_SPECS.
    """
    if arch is None:
        arch = get_host_arch()
    missing = set()
    augmented = 0
    for instance in dataset:
        if instance_ids is not None and instance["instance_id"] not in instance_ids:
            continue
        repo = instance["repo"]
        version = instance.get("version")
        specs = MAP_REPO_VERSION_TO_SPECS.get(repo, {}).get(version)
        if specs is None or "test_cmd" not in specs:
            missing.add((repo, version))
            continue
        instance["test_cmd"] = specs["test_cmd"]
        instance["image_name"] = _resolve_image_name(
            instance["instance_id"], specs, arch, namespace, instance_image_tag
        )
        augmented += 1

    if missing:
        pairs = ", ".join(f"{repo}@{version}" for repo, version in sorted(missing))
        raise ValueError(
            f"No test_cmd found in MAP_REPO_VERSION_TO_SPECS for: {pairs}"
        )
    return augmented


def main(
    dataset_path: str,
    output: str | None,
    instance_ids: list | None,
    arch: str | None,
    namespace: str | None,
    instance_image_tag: str,
) -> None:
    with open(dataset_path) as f:
        dataset = json.load(f)

    augmented = augment_dataset(
        dataset, instance_ids, arch, namespace, instance_image_tag
    )

    out_path = output or dataset_path
    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Added test_cmd + image_name to {augmented}/{len(dataset)} tasks → {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", help="Path to the dataset JSON file")
    parser.add_argument(
        "--output",
        default=None,
        help="Where to write the augmented dataset (default: in place)",
    )
    parser.add_argument(
        "--instance_ids",
        nargs="+",
        default=None,
        help="Only augment these instance IDs (default: all)",
    )
    parser.add_argument(
        "--arch",
        default=None,
        help="Architecture for image_name (default: host arch; per-repo "
        "docker_specs overrides still apply)",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Registry namespace prefix for image_name (default: none, i.e. "
        "local image)",
    )
    parser.add_argument(
        "--instance_image_tag",
        default=LATEST,
        help=f"Tag for image_name (default: {LATEST})",
    )
    args = parser.parse_args()
    main(
        args.dataset,
        args.output,
        args.instance_ids,
        args.arch,
        args.namespace,
        args.instance_image_tag,
    )
